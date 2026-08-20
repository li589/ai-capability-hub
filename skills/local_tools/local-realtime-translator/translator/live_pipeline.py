"""Live translation pipeline - main orchestrator.

Architecture:
  Mic → VAD → Paraformer Online (partial) → WebSocket
                └→ Qwen3-ASR (final) → WebSocket
                  → Hunyuan-1.8B-OV (iGPU) → WebSocket → MeloTTS → WebSocket
                  → Opus-MT (CPU fallback) → WebSocket → MeloTTS → WebSocket
"""

import sys
import time
import threading
import queue
import logging
import numpy as np
from pathlib import Path

import config
from translator.audio.capture import AudioCapture
from translator.audio.vad import VadEngine, SentenceManager, VadState
from translator.asr.streaming import StreamingAsr
from translator.asr.accurate import AccurateAsr
from translator.translation.hunyuan_ov import HunyuanOVTranslator
from translator.translation.opus_mt import OpusMTTranslator
from translator.tts.melotts import MeloTTSModel
from translator.server.ws_server import WsServer
from translator.messages import SentenceAudio, AsrResult
from translator.utils.audio import save_audio
from translator.utils.text import is_meaningful, clean_asr_text
from translator.utils import memdiag

logger = logging.getLogger(__name__)

OUTPUT_DIR = Path(__file__).parent.parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


class LivePipeline:
    """Main orchestrator. Wires audio → ASR → translation → TTS with threading."""

    def __init__(self, src_lang="zh", tgt_lang="en", enable_ws=True):
        self._src_lang = src_lang
        self._tgt_lang = tgt_lang
        self._enable_ws = enable_ws

        # Components
        self._capture = AudioCapture()
        self._vad = VadEngine()
        self._sentence_mgr = SentenceManager(self._vad)
        self._streaming_asr = StreamingAsr()
        self._accurate_asr = AccurateAsr()
        self._translator = HunyuanOVTranslator()
        self._fallback_translator = OpusMTTranslator()  # used when Hunyuan is unavailable
        self._tts = MeloTTSModel()
        self._ws_server = WsServer() if enable_ws else None

        # Queues for thread communication
        self._sentence_queue = queue.Queue()  # ASR final processing
        self._translation_queue = queue.Queue()  # Translation
        self._tts_queue = queue.Queue()  # TTS

        # State
        self._running = False
        self._in_sentence = False
        self._current_partial = ""
        self._sentence_count = 0
        # Assigned when a sentence starts (not when it ends) so the fast (asr1)
        # partials, accurate (asr2) partials and final all share one id and the
        # UI can update a single line in place. See _process_chunk.
        self._current_sentence_id = 0
        self._chunks_buf = []
        self._chunks_lock = threading.Lock()

    def load_models(self):
        """Load all models."""
        memdiag.stamp("load_models: start (frameworks imported)")

        print("  [1/5] Loading FSMN-VAD (endpoint detection)...")
        # VAD loaded in __init__ via FunASR AutoModel
        print("        [OK]")
        memdiag.stamp("after VAD (FSMN-VAD, loaded in __init__)")

        print("  [2/5] Loading Paraformer streaming (CPU)...")
        self._streaming_asr.load()
        print("        [OK]")
        memdiag.stamp("after Paraformer-Online + ct-punc preload")

        print("  [3/5] Loading Qwen3-ASR (iGPU)...")
        try:
            self._accurate_asr.load()
            print("        [OK]")
        except Exception as e:
            print(f"        [SKIP] {e}")
            print("        Will use Paraformer Offline as fallback")
        # When Qwen3-ASR is available it produces every final transcription, so
        # the offline Paraformer fallback is pure dead weight (~1.4GB resident).
        # Disable it so it is never lazily loaded. Only when Qwen3 is absent do
        # we keep the offline fallback live.
        if self._accurate_asr.available:
            self._streaming_asr.disable_offline()
            print("        Paraformer-Offline disabled (Qwen3 active) — saves ~1.4GB")
        memdiag.stamp("after Qwen3-ASR (iGPU/OpenVINO)")

        print(f"  [4/5] Loading Hunyuan-1.8B-OV ({self._src_lang}-{self._tgt_lang}, iGPU)...")
        hunyuan_ok = False
        try:
            self._translator.load()
            hunyuan_ok = True
            print("        [OK]")
        except Exception as e:
            print(f"        [SKIP] {e}")
        memdiag.stamp("after Hunyuan-1.8B-OV (iGPU/OpenVINO)")

        # Opus-MT fallback: load eagerly ONLY when Hunyuan is unavailable. When
        # Hunyuan loaded fine (the common case) Opus-MT is dead weight (~0.6GB);
        # it lazy-loads itself on first translate() call if Hunyuan ever fails
        # at runtime, so correctness is preserved without paying the memory cost
        # up front.
        if hunyuan_ok:
            print(f"  [4b/5] Opus-MT fallback: deferred (lazy-loads only if Hunyuan fails)")
        else:
            print(f"  [4b/5] Loading Opus-MT ({self._src_lang}→{self._tgt_lang}, primary — Hunyuan unavailable)...")
            try:
                self._fallback_translator.load(self._src_lang, self._tgt_lang)
                print("        [OK]")
            except Exception as e:
                print(f"        [FAIL] {e}")
        memdiag.stamp("after Opus-MT fallback (CPU)")

        if hunyuan_ok:
            print(f"        Translation engine: Hunyuan-1.8B-OV (iGPU), fallback Opus-MT (CPU, lazy)")
        else:
            print(f"        Translation engine: Opus-MT (CPU) — Hunyuan unavailable")

        print(f"  [5/5] Loading MeloTTS ({self._tgt_lang})...")
        try:
            self._tts.load(self._tgt_lang)
            print("        [OK]")
        except Exception as e:
            print(f"        [SKIP] {e}")
            self._tts = None
        memdiag.stamp("after MeloTTS (CPU) — ALL MODELS LOADED")

    def start(self):
        """Start all threads."""
        self._running = True

        if self._ws_server:
            self._ws_server.start()

        # Background threads
        threading.Thread(target=self._sentence_processor_loop, daemon=True).start()
        threading.Thread(target=self._translation_loop, daemon=True).start()
        threading.Thread(target=self._tts_loop, daemon=True).start()

        # Audio capture
        self._capture.add_listener(self._on_audio)
        self._capture.start()

        self._main_loop()

    def stop(self):
        self._running = False
        self._capture.stop()
        if self._ws_server:
            self._ws_server.stop()

    def _on_audio(self, samples: np.ndarray, timestamp_ms: int):
        with self._chunks_lock:
            self._chunks_buf.append((samples.copy(), timestamp_ms))

    def _main_loop(self):
        """Main thread: VAD + Paraformer Online streaming."""
        last_sample = time.time()
        try:
            while self._running:
                to_process = []
                with self._chunks_lock:
                    to_process = self._chunks_buf[:]
                    self._chunks_buf.clear()

                for samples, ts in to_process:
                    self._process_chunk(samples, ts)

                if not to_process:
                    time.sleep(0.005)

                # Periodic RSS sample (every 10s) to spot runtime growth vs a
                # stable plateau. No-op unless RT_MEMDIAG=1.
                if memdiag.enabled() and (time.time() - last_sample) >= 10.0:
                    last_sample = time.time()
                    memdiag.sample(
                        f"runtime: sentences={self._sentence_count} "
                        f"q[asr={self._sentence_queue.qsize()} "
                        f"trn={self._translation_queue.qsize()} "
                        f"tts={self._tts_queue.qsize()}]"
                    )
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()

    def _process_chunk(self, samples: np.ndarray, ts: int):
        """Process a single audio chunk through VAD + streaming ASR."""
        sentence_audio = self._sentence_mgr.feed(samples, ts)
        state = self._sentence_mgr.state

        if state == VadState.SPEECH or state == VadState.TRAILING_SILENCE:
            asr_result = None
            if not self._in_sentence:
                self._in_sentence = True
                # Number the sentence at its start so fast (asr1) partials,
                # accurate (asr2) partials and the final all carry the same id.
                self._sentence_count += 1
                self._current_sentence_id = self._sentence_count
                self._streaming_asr.start_sentence(ts)
                self._current_partial = ""
                # Seed streaming ASR with the VAD onset pre-buffer so the first
                # syllable (spoken before speech was confirmed) isn't dropped.
                # The onset already contains this chunk, so feed it instead of
                # `samples` to avoid duplicating the current block.
                onset = self._sentence_mgr.take_onset()
                if onset:
                    onset_audio = np.concatenate(onset)
                    asr_result = self._streaming_asr.feed(onset_audio, ts)
                else:
                    asr_result = self._streaming_asr.feed(samples, ts)
            else:
                asr_result = self._streaming_asr.feed(samples, ts)

            if asr_result and asr_result.text:
                self._current_partial = asr_result.text
                self._display_partial(asr_result.text)
                if self._ws_server:
                    self._ws_server.push_asr(
                        asr_result.text, is_final=False,
                        stage="fast", sentence_id=self._current_sentence_id,
                    )

        if sentence_audio is not None:
            final_partial = self._streaming_asr.end_sentence(ts)
            if final_partial and final_partial.text:
                self._current_partial = final_partial.text

            # sentence_id was assigned at sentence start (above); the offline
            # accurate pass reuses it so asr2 partials/final land on the same
            # UI line as the fast partials.
            self._in_sentence = False

            self._sentence_queue.put(
                (sentence_audio, self._current_partial, self._current_sentence_id)
            )
            self._current_partial = ""

    def _sentence_processor_loop(self):
        """Background: Qwen3-ASR (or Paraformer Offline fallback) → push final."""
        while self._running:
            try:
                item = self._sentence_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            sentence_audio, partial_text, sentence_num = item
            final_text = partial_text

            # Try Qwen3-ASR first (most accurate, streaming)
            if self._accurate_asr.available:
                try:
                    last_text = ""
                    for partial in self._accurate_asr.transcribe_stream(sentence_audio):
                        if partial:
                            last_text = partial
                            # Push partial to UI immediately (accurate/yellow,
                            # streaming in place on the same line as asr1)
                            if self._ws_server:
                                self._ws_server.push_asr(
                                    partial, is_final=False,
                                    stage="accurate", sentence_id=sentence_num,
                                )
                            # Console streaming display
                            sys.stdout.write(
                                f"\r  #{sentence_num} [Qwen3*] {partial}    "
                            )
                            sys.stdout.flush()
                    if last_text:
                        final_text = last_text
                        # Clear streaming line
                        sys.stdout.write("\r" + " " * 80 + "\r")
                        sys.stdout.flush()
                except Exception:
                    import traceback
                    traceback.print_exc()
            else:
                # Fallback: Paraformer Offline
                result = self._streaming_asr.finalize_offline(sentence_audio)
                if result and result.text:
                    final_text = result.text

            # Clean ASR stutters/hallucinated repetitions, then drop empty /
            # punctuation-only / ultra-short noise transcriptions before they
            # reach translation + TTS. Such fragments come from spurious VAD
            # segments and otherwise produce empty translation bubbles and
            # garbage audio files.
            final_text = clean_asr_text(final_text)
            if not is_meaningful(final_text):
                continue

            # Push final ASR to UI (accurate/yellow, settles the line)
            self._display_final(final_text, sentence_num)
            if self._ws_server:
                self._ws_server.push_asr(
                    final_text, is_final=True,
                    stage="accurate", sentence_id=sentence_num,
                )

            # Send to translation
            self._translation_queue.put((final_text, sentence_num))

    def _translation_loop(self):
        """Background: Hunyuan translation (iGPU, streaming) with Opus-MT fallback."""
        while self._running:
            try:
                item = self._translation_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            text, sentence_num = item
            translated = None
            engine = ""
            last_partial = ""           # best partial Hunyuan streamed, if any
            partial_pushed = False      # did we create an in-progress UI bubble?

            # Try Hunyuan first with streaming (high quality, iGPU)
            if self._translator.available:
                try:
                    for partial in self._translator.translate_stream(
                        text, self._src_lang, self._tgt_lang
                    ):
                        if partial:
                            last_partial = partial
                            # Push partial to UI
                            if self._ws_server:
                                self._ws_server.push_translation_partial(
                                    partial, self._src_lang, self._tgt_lang, sentence_num
                                )
                                partial_pushed = True
                            # Console display — use \r to overwrite
                            sys.stdout.write(
                                f"\r  #{sentence_num} [Hunyuan*] {partial}    "
                            )
                            sys.stdout.flush()

                    if last_partial:
                        translated = last_partial
                        engine = "Hunyuan"
                        # Clear the streaming line
                        sys.stdout.write("\r" + " " * 80 + "\r")
                        sys.stdout.flush()
                except Exception as e:
                    logger.warning(f"Hunyuan streaming failed, fallback to Opus-MT: {e}")

            # Fallback to Opus-MT (CPU, no streaming)
            if not translated:
                try:
                    translated = self._fallback_translator.translate(
                        text, self._src_lang, self._tgt_lang
                    )
                    if translated:
                        engine = "Opus-MT"
                except Exception as e:
                    logger.error(f"Translation failed: {e}")

            if translated:
                self._display_translation(translated, sentence_num, engine)
                if self._ws_server:
                    self._ws_server.push_translation(
                        translated, self._src_lang, self._tgt_lang, sentence_num
                    )
                # Send to TTS
                self._tts_queue.put((translated, sentence_num))
            elif partial_pushed and self._ws_server:
                # Both engines failed to produce a final translation, but we
                # already created an in-progress (italic) bubble during Hunyuan
                # streaming. Settle it to a final state so it does not linger
                # forever as a half-translated artifact. Emit the best partial we
                # have (or empty to clear) — without this the UI shows a stuck
                # italic bubble for a sentence that never completed.
                self._ws_server.push_translation(
                    last_partial, self._src_lang, self._tgt_lang, sentence_num
                )

    def _tts_loop(self):
        """Background: MeloTTS synthesis."""
        while self._running:
            try:
                item = self._tts_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            text, sentence_num = item
            if self._tts is None:
                continue

            try:
                audio = self._tts.synthesize(text, language=self._tgt_lang, speed=config.TTS_SPEED)
                if len(audio) > 0:
                    filename = f"sentence_{sentence_num:04d}.wav"
                    output_path = str(OUTPUT_DIR / filename)
                    save_audio(audio, output_path, self._tts.sample_rate)
                    if self._ws_server:
                        self._ws_server.push_tts(filename, sentence_num)
                    self._display_tts(output_path, sentence_num)
                    # Keep the output dir bounded so a long session doesn't fill
                    # the disk. Done after push_tts so the just-written file is
                    # never pruned before the UI is told about it.
                    self._prune_output_wavs()
            except Exception as e:
                logger.error(f"TTS failed: {e}")

    @staticmethod
    def _prune_output_wavs():
        """Delete the oldest sentence_*.wav so at most TTS_OUTPUT_KEEP remain.

        Ordered by modification time (robust past 9999 sentences, where the
        zero-padded filename would otherwise sort wrong). Best-effort: any
        per-file removal error is ignored so pruning never breaks TTS.
        """
        keep = getattr(config, "TTS_OUTPUT_KEEP", 0)
        if not keep or keep <= 0:
            return
        try:
            wavs = sorted(
                OUTPUT_DIR.glob("sentence_*.wav"),
                key=lambda p: p.stat().st_mtime,
            )
        except OSError:
            return
        for old in wavs[:-keep]:
            try:
                old.unlink()
            except OSError:
                pass

    def _display_partial(self, text: str):
        sys.stdout.write(f"\r  [partial] {text}    ")
        sys.stdout.flush()

    def _display_final(self, text: str, sentence_num: int):
        sys.stdout.write(f"\r  #{sentence_num} [ASR] {text}\n")
        sys.stdout.flush()

    def _display_translation(self, text: str, sentence_num: int, engine: str = ""):
        tag = f"[{engine}] " if engine else ""
        sys.stdout.write(f"  #{sentence_num} {tag}[TRN] {text}\n")
        sys.stdout.flush()

    def _display_tts(self, path: str, sentence_num: int):
        sys.stdout.write(f"  #{sentence_num} [TTS] {path}\n")
        sys.stdout.flush()
