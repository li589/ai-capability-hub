"""推理执行模块：处理 VLM 推理的核心逻辑。"""
from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Optional

import numpy as np
import openvino_genai as ov_genai
from PIL import Image

from .constants import DEFAULT_MAX_NEW_TOKENS
from .utils import pil_to_ov_tensor

logger = logging.getLogger(__name__)

_CPU_WORKERS = 4


class InferenceEngine:
    """OpenVINO VLMPipeline 推理引擎封装。"""

    def __init__(
        self,
        model_dir: str,
        device: str,
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
        ov_config: Optional[dict] = None,
        performance_hint: str = "LATENCY",
        enable_warmup: bool = True,
    ):
        """初始化推理引擎。

        Parameters
        ----------
        model_dir        : OpenVINO IR 模型目录
        device           : 推理设备
        max_new_tokens   : 最大新 token 数
        ov_config        : OpenVINO 额外配置
        performance_hint : "LATENCY" 或 "THROUGHPUT" (多页时推荐 THROUGHPUT)
        enable_warmup    : 是否执行预热推理
        """
        self.model_dir = Path(model_dir)
        self.device = device
        self._max_new_tokens = max_new_tokens
        self._is_npu = "NPU" in device.upper()
        self._is_gpu = "GPU" in device.upper()
        self._is_cpu = "CPU" in device.upper()
        self._hint = performance_hint.upper()

        _ov_cfg = self._build_ov_config(ov_config)

        t_load = time.time()
        self.pipe = ov_genai.VLMPipeline(str(self.model_dir), device=device, **_ov_cfg)
        logger.info("VLMPipeline loaded in %.1fs", time.time() - t_load)

        if enable_warmup:
            self._warmup()

    def _build_ov_config(self, ov_config: Optional[dict]) -> dict:
        """构建 OpenVINO 运行时配置。"""
        from .constants import NPU_MAX_PROMPT_LEN

        cfg: dict = {}

        hint = self._hint if self._hint in ("LATENCY", "THROUGHPUT", "UNDEFINED") else "LATENCY"

        if self._is_gpu:
            if hint == "THROUGHPUT":
                cfg.setdefault("PERFORMANCE_HINT", "THROUGHPUT")
                cfg.setdefault("GPU_THROUGHPUT_STREAMS", "2")
            else:
                cfg.setdefault("PERFORMANCE_HINT", "LATENCY")
            logger.info("GPU 配置: PERFORMANCE_HINT=%s", cfg.get("PERFORMANCE_HINT"))

        elif self._is_cpu:
            if hint == "THROUGHPUT":
                cfg.setdefault("PERFORMANCE_HINT", "THROUGHPUT")
                cfg.setdefault("NUM_STREAMS", "0")
                cfg.setdefault("INFERENCE_NUM_THREADS", "0")
            else:
                cfg.setdefault("PERFORMANCE_HINT", "LATENCY")
                cfg.setdefault("NUM_STREAMS", "1")
                cfg.setdefault("CPU_THROUGHPUT_STREAMS", "AUTO")
                cfg.setdefault("INFERENCE_NUM_THREADS", "0")
            logger.info("CPU 配置: PERFORMANCE_HINT=%s", cfg.get("PERFORMANCE_HINT"))

        elif self._is_npu:
            cfg["MAX_PROMPT_LEN"] = NPU_MAX_PROMPT_LEN
            cfg.setdefault("PERFORMANCE_HINT", "LATENCY")

            if self._max_new_tokens > 2048:
                logger.warning(
                    "NPU: max_new_tokens %d -> 2048 to avoid timeout",
                    self._max_new_tokens
                )
                self._max_new_tokens = 2048

            cache_dir = self.model_dir / ".ov_npu_cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            cfg.setdefault("CACHE_DIR", str(cache_dir))
            logger.info("NPU 配置: PERFORMANCE_HINT=LATENCY, 编译缓存: %s", cache_dir)
        else:
            cfg.setdefault("PERFORMANCE_HINT", hint)

        if ov_config:
            cfg.update(ov_config)

        return cfg

    def _warmup(self) -> None:
        """执行一次空推理预热，触发 JIT 编译，避免首页耗时过长。"""
        try:
            t0 = time.time()
            dummy = np.zeros((1, 224, 224, 3), dtype=np.uint8)
            import openvino as ov
            self.pipe.generate("", image=ov.Tensor(dummy), generation_config=ov_genai.GenerationConfig())
            logger.info("预热推理完成，耗时 %.1fs", time.time() - t0)
        except Exception as e:
            logger.debug("预热推理跳过: %s", e)

    def generate(
        self,
        image: Image.Image,
        prompt: str,
        generation_config: Optional[ov_genai.GenerationConfig] = None,
    ) -> str:
        """对图像执行推理（同步模式）。

        Parameters
        ----------
        image              : PIL Image
        prompt             : 提示词
        generation_config  : 生成配置

        Returns
        -------
        str: 生成的文本
        """
        tensor = pil_to_ov_tensor(image)
        t0 = time.time()
        result = self.pipe.generate(prompt, image=tensor, generation_config=generation_config)
        logger.debug("Inference done in %.2fs", time.time() - t0)
        return str(result)

    def unload(self) -> None:
        """释放推理引擎资源。"""
        self.pipe = None
        logger.info("InferenceEngine unloaded")


# ═══════════════════════════════════════════════════════════════
# BatchInferenceEngine — 基于 ContinuousBatchingPipeline
# ═══════════════════════════════════════════════════════════════


class BatchInferenceEngine:
    """基于 ContinuousBatchingPipeline 的高吞吐推理引擎。

    通过 add_request() 批量提交推理请求，continuous batching 调度器
    动态批处理 token 生成步骤。单模型实例即可高效处理多个并发请求。

    v20 optimizations:
      - Tokenizer cached at init (avoid per-call lookup)
      - Token decoding parallelized via ThreadPoolExecutor
      - Warmup uses layout prompt for realistic kernel compilation
      - Small N skips thread pool (sequential is faster)
    """

    def __init__(
        self,
        model_dir: str,
        device: str,
        max_concurrent: int = 8,
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
        ov_config: Optional[dict] = None,
        enable_warmup: bool = True,
        warmup_prompt: str = "",
    ):
        self.model_dir = Path(model_dir)
        self.device = device
        self._max_new_tokens = max_new_tokens
        self._next_req_id = 0
        self._warmup_prompt = warmup_prompt

        is_npu = "NPU" in device.upper()

        scheduler_config = ov_genai.SchedulerConfig()
        scheduler_config.max_num_seqs = max_concurrent
        scheduler_config.dynamic_split_fuse = True

        _properties: dict = {}
        if is_npu:
            from .constants import NPU_MAX_PROMPT_LEN
            scheduler_config.max_num_seqs = min(max_concurrent, 4)
            _properties["MAX_PROMPT_LEN"] = NPU_MAX_PROMPT_LEN
            cache_dir = self.model_dir / ".ov_npu_cache"
            cache_dir.mkdir(parents=True, exist_ok=True)
            _properties.setdefault("CACHE_DIR", str(cache_dir))
        else:
            _properties.setdefault("PERFORMANCE_HINT", "LATENCY")

        if ov_config:
            _properties.update(ov_config)

        t_load = time.time()
        self.pipe = ov_genai.ContinuousBatchingPipeline(
            str(self.model_dir),
            scheduler_config,
            device=device,
            properties=_properties,
        )
        logger.info("ContinuousBatchingPipeline loaded in %.1fs", time.time() - t_load)

        self._tokenizer = self.pipe.get_tokenizer()

        if enable_warmup:
            self._warmup()

    def _warmup(self) -> None:
        try:
            t0 = time.time()
            dummy = Image.new("RGB", (64, 64), color=(255, 255, 255))
            tensor = pil_to_ov_tensor(dummy)
            cfg = ov_genai.GenerationConfig()
            cfg.max_new_tokens = 1
            cfg.do_sample = False
            prompt = self._warmup_prompt or ""
            rid = self._next_req_id
            self._next_req_id += 1
            handle = self.pipe.add_request(rid, prompt, images=[tensor], generation_config=cfg)
            while self.pipe.has_non_finished_requests():
                self.pipe.step()
            _ = handle.read_all()
            logger.info("预热推理完成，耗时 %.1fs", time.time() - t0)
        except Exception as e:
            logger.debug("预热推理跳过: %s", e)

    def batch_generate(
        self,
        items: list[tuple[Image.Image, str, ov_genai.GenerationConfig]],
    ) -> list[str]:
        """批量执行推理并返回解码文本。

        Parameters
        ----------
        items : list of (image, prompt, generation_config)

        Returns
        -------
        list[str]: 解码后的文本，与输入顺序一致
        """
        if not items:
            return []
        handles = []
        for offset, (img, prompt, cfg) in enumerate(items):
            tensor = pil_to_ov_tensor(img)
            req_id = self._next_req_id + offset
            handle = self.pipe.add_request(
                req_id, prompt, images=[tensor], generation_config=cfg,
            )
            handles.append((req_id, handle))
        self._next_req_id += len(items)

        while self.pipe.has_non_finished_requests():
            self.pipe.step()

        return self._decode_handles(handles)

    def decode_handle(self, handle) -> str:
        outputs = handle.read_all()
        if not outputs:
            return ""
        return self._tokenizer.decode(outputs[0].generated_ids)

    def _decode_handles(self, handles: list) -> list[str]:
        tokenizer = self._tokenizer

        def _decode_one(item: tuple[int, object]) -> tuple[int, str]:
            req_id, handle = item
            outputs = handle.read_all()
            texts = [tokenizer.decode(o.generated_ids) for o in outputs]
            return (req_id, texts[0] if texts else "")

        if len(handles) <= 2:
            results = [_decode_one(h) for h in handles]
        else:
            with ThreadPoolExecutor(max_workers=min(_CPU_WORKERS, len(handles))) as pool:
                results = list(pool.map(_decode_one, handles))

        results.sort(key=lambda x: x[0])
        return [r[1] for r in results]

    def generate(
        self,
        image: Image.Image,
        prompt: str,
        generation_config: Optional[ov_genai.GenerationConfig] = None,
    ) -> str:
        """单次推理（委托给 batch_generate）。"""
        return self.batch_generate([(image, prompt, generation_config)])[0]

    def unload(self) -> None:
        self.pipe = None
        logger.info("BatchInferenceEngine unloaded")


_GEN_CONFIG_CACHE: dict = {}


def build_generation_config(
    sampling_params,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
) -> ov_genai.GenerationConfig:
    """将 MinerU SamplingParams 转换为 OpenVINO GenerationConfig。

    结果会被缓存，避免反复创建相同的 GenerationConfig 对象。

    Parameters
    ----------
    sampling_params : MinerU SamplingParams 对象或 None
    max_new_tokens  : 最大新 token 数

    Returns
    -------
    ov_genai.GenerationConfig: OpenVINO 生成配置
    """
    if sampling_params is None:
        cache_key = ("__none__", max_new_tokens)
    else:
        cache_key = (
            getattr(sampling_params, "temperature", 0.0),
            getattr(sampling_params, "top_p", 1.0),
            getattr(sampling_params, "top_k", 0),
            getattr(sampling_params, "repetition_penalty", 1.0),
            getattr(sampling_params, "max_new_tokens", max_new_tokens),
        )

    cached = _GEN_CONFIG_CACHE.get(cache_key)
    if cached is not None:
        return cached

    cfg = ov_genai.GenerationConfig()
    cfg.max_new_tokens = (
        getattr(sampling_params, "max_new_tokens", None) or max_new_tokens
    )

    if sampling_params is None:
        cfg.do_sample = False
    else:
        temperature = getattr(sampling_params, "temperature", None)
        top_k = getattr(sampling_params, "top_k", None)
        do_sample = (temperature or 0.0) > 0.0 and (top_k or 1) > 1
        cfg.do_sample = do_sample

        if do_sample:
            if temperature is not None:
                cfg.temperature = float(temperature)
            top_p = getattr(sampling_params, "top_p", None)
            if top_p is not None:
                cfg.top_p = float(top_p)
            if top_k is not None:
                cfg.top_k = int(top_k)

        rep = getattr(sampling_params, "repetition_penalty", None)
        if rep is not None:
            cfg.repetition_penalty = float(rep)

        presence = getattr(sampling_params, "presence_penalty", None)
        if presence is not None:
            try:
                cfg.presence_penalty = float(presence)
            except AttributeError:
                pass

        freq = getattr(sampling_params, "frequency_penalty", None)
        if freq is not None:
            try:
                cfg.frequency_penalty = float(freq)
            except AttributeError:
                pass

        ngram = getattr(sampling_params, "no_repeat_ngram_size", None)
        if ngram is not None:
            try:
                cfg.no_repeat_ngram_size = int(ngram)
            except AttributeError:
                pass

    _GEN_CONFIG_CACHE[cache_key] = cfg
    return cfg
