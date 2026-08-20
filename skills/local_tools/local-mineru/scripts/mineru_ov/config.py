"""设备与精度配置管理器。

优先级：CLI 参数 > 环境变量 > 配置文件 > 内置默认值
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml
from loguru import logger

from .constants import SUPPORTED_DEVICES, SUPPORTED_PRECISIONS, NPU_REQUIRED_PRECISION
from .constants import VLM_MODEL_BASENAME, VLM_MODEL_INT4_SUFFIX


def _get_openvino_models_dir() -> Path:
    """返回 OpenVINO 模型目录：~/.openvino/models/mineru-ov-models/。"""
    env_dir_str = os.environ.get("OPENVINO_DIR", "")
    if env_dir_str:
        return Path(env_dir_str) / "models" / "mineru-ov-models"
    return Path.home() / ".openvino" / "models" / "mineru-ov-models"


_PROJECT_ROOT = Path(__file__).parent.parent.parent
_DEFAULT_CONFIG_PATH = _PROJECT_ROOT / "configs" / "default_config.yaml"
_DEFAULT_MODELS_DIR = _get_openvino_models_dir()


@dataclass
class OVConfig:
    device: str = "GPU"
    precision: str = "int4"
    models_dir: str = ""
    pdf_dpi: int = 150
    layout_image_size: tuple[int, int] = field(default_factory=lambda: (1036, 1036))
    max_new_tokens: int = 2048
    layout_max_new_tokens: int = 1024
    npu_max_new_tokens: int = 2048
    image_analysis: bool = False
    batch_size: int = 1
    webui_port: int = 7878
    parallel_pages: int = 1
    enable_warmup: bool = True
    performance_hint: str = "LATENCY"
    use_batch_backend: bool = False
    max_concurrent: int = 8
    backend_type: str = "vlm"
    ov_config: Optional[dict] = None

    @property
    def model_dir(self) -> Path:
        """返回模型目录的绝对路径。

        - 用户指定了 models_dir 时：直接使用用户路径
        - 用户未指定时：使用 ~/.openvino/models/mineru-ov-models/
        """
        if self.models_dir:
            return Path(self.models_dir).resolve()
        return _DEFAULT_MODELS_DIR

    @property
    def vlm_model_dir(self) -> Path:
        base = self.model_dir
        return base / (VLM_MODEL_BASENAME + VLM_MODEL_INT4_SUFFIX)

    @classmethod
    def from_yaml(cls, path: str | Path) -> "OVConfig":
        """从 YAML 文件加载配置。"""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls._from_dict(data)

    @classmethod
    def load(
        cls,
        config_path: Optional[str] = None,
        *,
        device: Optional[str] = None,
        precision: Optional[str] = None,
        models_dir: Optional[str] = None,
        **overrides,
    ) -> "OVConfig":
        """按优先级加载配置：

        1. 默认配置文件 (configs/default_config.yaml)
        2. 用户指定配置文件
        3. CLI 参数（device, precision 等关键字参数，最高优先级）
        """
        cfg_data: dict = {}
        if _DEFAULT_CONFIG_PATH.exists():
            with open(_DEFAULT_CONFIG_PATH, "r", encoding="utf-8") as f:
                cfg_data = yaml.safe_load(f) or {}

        if config_path:
            user_path = Path(config_path)
            if user_path.exists():
                with open(user_path, "r", encoding="utf-8") as f:
                    user_data = yaml.safe_load(f) or {}
                cfg_data.update(user_data)
            else:
                logger.warning("User config not found: {}", config_path)

        if device:
            cfg_data["device"] = device
        if precision:
            cfg_data["precision"] = precision
        if models_dir:
            cfg_data["models_dir"] = models_dir
        cfg_data.update(overrides)

        obj = cls._from_dict(cfg_data)
        obj.validate()
        return obj

    @classmethod
    def _from_dict(cls, data: dict) -> "OVConfig":
        """从字典创建配置实例。"""
        layout_size = data.get("layout_image_size", [1036, 1036])
        if isinstance(layout_size, list):
            layout_size = tuple(layout_size)
        return cls(
            device=str(data.get("device", "GPU")).upper(),
            precision=str(data.get("precision", "int4")).lower(),
            models_dir=str(data.get("models_dir", "")),
            pdf_dpi=int(data.get("pdf_dpi", 150)),
            layout_image_size=layout_size,
            max_new_tokens=int(data.get("max_new_tokens", 2048)),
            layout_max_new_tokens=int(data.get("layout_max_new_tokens", 1024)),
            npu_max_new_tokens=int(data.get("npu_max_new_tokens", 2048)),
            image_analysis=bool(data.get("image_analysis", False)),
            batch_size=int(data.get("batch_size", 1)),
            webui_port=int(data.get("webui_port", 7878)),
            parallel_pages=int(data.get("parallel_pages", 1)),
            enable_warmup=bool(data.get("enable_warmup", True)),
            performance_hint=str(data.get("performance_hint", "LATENCY")),
            use_batch_backend=bool(data.get("use_batch_backend", False)),
            max_concurrent=int(data.get("max_concurrent", 8)),
            backend_type=str(data.get("backend_type", "vlm")).lower(),
            ov_config=data.get("ov_config"),
        )

    def validate(self) -> None:
        """验证配置合理性，必要时自动修正。

        修正行为：
        - NPU 设备自动切换精度为 int4
        - 不支持的精度会抛出 ValueError
        """
        primary = self.device.split(":")[0].upper()

        if primary == "NPU" and self.precision != "int4":
            logger.warning(
                "NPU 设备要求 int4 精度，已自动从 '{}' 切换为 'int4'。",
                self.precision,
            )
            self.precision = "int4"

        if self.precision not in SUPPORTED_PRECISIONS:
            raise ValueError(
                f"不支持的精度 '{self.precision}'，请选择 {SUPPORTED_PRECISIONS}"
            )

        if self.model_dir.exists():
            xml_files = list(self.model_dir.rglob("*.xml"))
            if not xml_files:
                logger.warning(
                    "模型目录 {} 中未找到 .xml 文件，请先运行模型转换脚本。",
                    self.model_dir,
                )
        else:
            logger.info(
                "模型目录 {} 不存在，将在首次推理时自动转换或下载。",
                self.model_dir,
            )

    def to_dict(self) -> dict:
        """导出配置为字典（用于日志和调试）。"""
        return {
            "device": self.device,
            "precision": self.precision,
            "models_dir": self.models_dir,
            "pdf_dpi": self.pdf_dpi,
            "layout_image_size": list(self.layout_image_size),
            "max_new_tokens": self.max_new_tokens,
            "layout_max_new_tokens": self.layout_max_new_tokens,
            "npu_max_new_tokens": self.npu_max_new_tokens,
            "image_analysis": self.image_analysis,
            "batch_size": self.batch_size,
            "webui_port": self.webui_port,
            "parallel_pages": self.parallel_pages,
            "enable_warmup": self.enable_warmup,
            "performance_hint": self.performance_hint,
            "use_batch_backend": self.use_batch_backend,
            "max_concurrent": self.max_concurrent,
            "backend_type": self.backend_type,
            "ov_config": self.ov_config,
            "model_dir_resolved": str(self.model_dir),
        }

    def __str__(self) -> str:
        return (
            f"OVConfig(device={self.device}, precision={self.precision}, "
            f"model_dir={self.model_dir})"
        )
