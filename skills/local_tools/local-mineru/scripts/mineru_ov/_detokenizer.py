"""MinerU Detokenizer 修补模块。

处理 MinerU 版面检测输出中使用的特殊 token，
确保 OpenVINO detokenizer 在解码时保留这些 token。
"""
from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Union

from .constants import MINERU_OUTPUT_TOKENS

logger = logging.getLogger(__name__)


def patch_detokenizer_for_mineru(
    model_dir: Union[str, Path],
    hf_model_id_or_path: Union[str, Path],
) -> None:
    """重新导出 OpenVINO detokenizer，使 MinerU 版面 token 在解码时保留。

    后续调用为空操作（通过标记文件 .mineru_detokenizer_patched 判断）。

    Parameters
    ----------
    model_dir           : 已导出的 OpenVINO IR 模型目录
    hf_model_id_or_path : 原始 HF 模型 ID 或本地路径（用于读取 tokenizer）
    """
    try:
        from transformers import AutoTokenizer
        from openvino_tokenizers import convert_tokenizer
        from tokenizers import AddedToken
    except ImportError as e:
        logger.warning("无法修补 detokenizer（缺少依赖）: {}", e)
        return

    import openvino as ov

    model_dir = Path(model_dir)
    marker = model_dir / ".mineru_detokenizer_patched"

    token_hash = hashlib.md5("|".join(MINERU_OUTPUT_TOKENS).encode()).hexdigest()[:8]
    if marker.exists() and marker.read_text().strip() == token_hash:
        logger.info("Detokenizer already patched (hash=%s), skipping", token_hash)
        return

    logger.info("Patching OpenVINO detokenizer for MinerU layout tokens ...")
    tokenizer = AutoTokenizer.from_pretrained(str(hf_model_id_or_path))
    for tok in MINERU_OUTPUT_TOKENS:
        tokenizer._tokenizer.add_tokens(
            [AddedToken(tok, special=False, normalized=False)]
        )
    _, ov_detok = convert_tokenizer(tokenizer, with_detokenizer=True)
    ov.save_model(ov_detok, str(model_dir / "openvino_detokenizer.xml"))
    marker.write_text(token_hash)
    logger.info("Detokenizer patched and saved to %s", model_dir)
