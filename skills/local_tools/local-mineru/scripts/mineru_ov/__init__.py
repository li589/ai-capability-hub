"""MinerU-OV: MinerU2.5-Pro × OpenVINO 推理加速项目。

提供文档解析（PDF/图像）的 VLM 与 Hybrid 推理后端。

公开 API:
  - OVConfig           配置管理器
  - MinerUPipeline     主推理管道
  - OVMinerUClient     VLM 后端客户端 (vlm_backend)
  - OVHybridClient     Hybrid 后端客户端 (hybrid_backend)
  - OVLayoutModel      PP-DocLayoutV2 版面检测
  - OVMFRModel         UniMerNet 公式识别
  - OVOCREngine        PP-OCRv5 检测+识别
"""

from .config import OVConfig
from .pipeline import MinerUPipeline
from .vlm_backend import OVMinerUClient, BatchMinerUClient
from .hybrid_backend import OVHybridClient
from .pipeline_models import OVLayoutModel, OVMFRModel, OVOCREngine
from . import config, constants, post_process, pdf_utils, utils, vlm_backend

__all__ = [
    "OVConfig",
    "MinerUPipeline",
    "OVMinerUClient",
    "BatchMinerUClient",
    "OVHybridClient",
    "OVLayoutModel",
    "OVMFRModel",
    "OVOCREngine",
]
