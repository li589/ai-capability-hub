# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Intel OBL

"""vlm_engine.py — OpenVINO inference engine for Qwen3-VL.

Inference only — no model conversion. Kept thin on purpose: the heavy work
happens inside ``optimum.intel.OVModelForVisualText2Text``; this module just
wires input/output and exposes a small ``OVQwen3VLModel`` facade that mirrors the
``asr_engine`` shape (``from_pretrained`` + a single inference method) so
``server.py`` can load it once and keep it resident.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

ENGINE_VERSION = "v1.0"

# Generation defaults — preserved from the source skill's config/models.json.
DEFAULT_MAX_NEW_TOKENS = 512


def build_pipeline(model_path: Path, device: str = "AUTO") -> Any:
    """Construct the Qwen3-VL pipeline.

    Imports are deferred so this module stays importable under a plain Python
    interpreter with no OpenVINO / optimum-intel installed (host-side unit tests
    import the server's siblings without the heavy runtime).
    """
    # Late imports — these are heavy and only present under the venv.
    from PIL import Image  # noqa: F401  (pillow is in requirements.txt)
    from transformers import AutoProcessor  # type: ignore[import-untyped]

    try:
        from optimum.intel import OVModelForVisualText2Text  # type: ignore[import-untyped]
    except ImportError:
        # The shipped optimum-intel build (1.27.0.dev0+2f62e5a, vendored under
        # wheels/) exports OVModelForVisualText2Text and is the build validated on
        # an Intel AIPC for Qwen3-VL. This fallback to the older OVModelForVisualCausalLM
        # name keeps the module importable across optimum-intel naming changes.
        from optimum.intel import OVModelForVisualCausalLM as OVModelForVisualText2Text  # type: ignore[import-untyped]

    model = OVModelForVisualText2Text.from_pretrained(
        str(model_path),
        device=device,
        ov_config={"PERFORMANCE_HINT": "LATENCY"},
    )
    processor = AutoProcessor.from_pretrained(str(model_path), trust_remote_code=True)
    return {"model": model, "processor": processor, "device": device}


def run_generate(
    pipe: Any,
    *,
    question: str,
    image_path: str,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
) -> str:
    from PIL import Image  # type: ignore[import-untyped]

    img = Image.open(image_path).convert("RGB")
    processor = pipe["processor"]
    model = pipe["model"]
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": question},
            ],
        }
    ]
    text = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
    inputs = processor(text=[text], images=[img], return_tensors="pt")
    output_ids = model.generate(**inputs, max_new_tokens=max_new_tokens)
    decoded = processor.batch_decode(output_ids, skip_special_tokens=True)[0]
    # Strip the prompt prefix so we only return the model's answer.
    return decoded[len(text):].strip() if decoded.startswith(text) else decoded.strip()


class OVQwen3VLModel:
    """Resident Qwen3-VL pipeline facade.

    Mirrors ``asr_engine.OVQwen3ASRModel``: built once via ``from_pretrained`` and
    kept loaded by ``server.py`` across requests.
    """

    def __init__(self, model_dir, device: str = "AUTO", max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS):
        self.model_dir = Path(model_dir)
        self.device = device
        self.max_new_tokens = max_new_tokens
        self.pipe = build_pipeline(self.model_dir, device=device)

    @classmethod
    def from_pretrained(
        cls,
        model_dir,
        device: str = "AUTO",
        max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
        **kw,
    ) -> "OVQwen3VLModel":
        return cls(model_dir=model_dir, device=device, max_new_tokens=max_new_tokens)

    def generate(self, *, question: str, image_path: str, max_new_tokens: int | None = None) -> str:
        return run_generate(
            self.pipe,
            question=question,
            image_path=image_path,
            max_new_tokens=max_new_tokens if max_new_tokens is not None else self.max_new_tokens,
        )
