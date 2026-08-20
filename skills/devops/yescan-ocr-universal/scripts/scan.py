#!/usr/bin/env python3
"""
Quark OCR - 夸克扫描王 OCR 识别服务
支持图片 URL、本地文件路径（自动转 BASE64）、BASE64 字符串
"""
import argparse
import json
import os
import sys
import base64
import binascii
import logging
from typing import Tuple, Dict, Any, Optional
from dataclasses import dataclass
from urllib.parse import urlparse

import requests
from requests.exceptions import Timeout, ConnectionError, RequestException

# --- 配置常量 ---
# API 配置
API_URL = "https://scan-business.quark.cn/vision"
DEFAULT_API_KEY_ENV = "SCAN_WEBSERVICE_KEY"

# 文件配置
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".tif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# 请求配置
REQUEST_TIMEOUT = int(os.getenv("SCAN_REQUEST_TIMEOUT", "120"))  # 秒
MAX_RETRY_TIMES = int(os.getenv("SCAN_MAX_RETRY_TIMES", "3"))  # 最大重试次数

# 响应码常量
SUCCESS_CODE = "00000"

# 错误码消息常量
ERR_MSG_A0211_QUOTA_INSUFFICIENT = "请前往https://scan.quark.cn/business，登录开发者后台，选择需要的套餐进行充值（请注意购买Skill专用套餐）"

# 错误码常量
ERR_INVALID_INPUT = "INVALID_INPUT"
ERR_URL_VALIDATION = "URL_VALIDATION_ERROR"
ERR_BASE64_FORMAT = "BASE64_FORMAT_ERROR"
ERR_BASE64_PARSE = "BASE64_PARSE_ERROR"
ERR_BASE64_DECODE = "BASE64_DECODE_ERROR"
ERR_FILE_ERROR = "FILE_ERROR"
ERR_FILE_READ = "FILE_READ_ERROR"
ERR_HTTP_ERROR = "HTTP_ERROR"
ERR_JSON_PARSE = "JSON_PARSE_ERROR"
ERR_INVALID_JSON = "INVALID_JSON"
ERR_CONFIG_ERROR = "CONFIG_ERROR"
ERR_TIMEOUT = "TIMEOUT"
ERR_NETWORK_ERROR = "NETWORK_ERROR"
ERR_UNKNOWN_ERROR = "UNKNOWN_ERROR"

# 配置日志
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """OCR 识别结果 - 直接返回 API 原始响应"""
    code: str
    message: Optional[str]
    data: Optional[Dict[str, Any]]  # 原始 API 返回的 data 字段

    def to_json(self) -> str:
        """返回完整的 API 响应结构"""
        return json.dumps({
            "code": self.code,
            "message": self.message,
            "data": self.data
        }, ensure_ascii=False, indent=2)

class URLValidator:
    """URL 基础验证器"""

    @staticmethod
    def validate(url: str) -> Tuple[bool, Optional[str]]:
        if not url or not isinstance(url, str):
            return False, "URL cannot be empty"

        url = url.strip()

        try:
            parsed = urlparse(url)
        except ValueError as e:
            return False, f"Invalid URL format: {str(e)}"

        if parsed.scheme.lower() not in {"http", "https"}:
            return False, f"Protocol '{parsed.scheme}' not allowed."

        return True, None

class CredentialManager:
    """凭证管理器，负责加载和验证 API 密钥"""

    @staticmethod
    def load() -> str:
        """
        从环境变量加载 API 密钥

        Returns:
            str: API 密钥

        Raises:
            ValueError: 当环境变量未配置或为空时抛出
        """
        api_key = os.getenv(DEFAULT_API_KEY_ENV, "").strip()
        if api_key:
            return api_key

        error_msg = (
            "⚠️ 环境变量 SCAN_WEBSERVICE_KEY 未配置\n\n"
            "夸克扫描王 OCR 服务需要 API Key 才能使用。\n\n"
            "🔧 如何获取密钥？官方入口在此：\n"
            "请访问 https://scan.quark.cn/business → 开发者后台 → 登录/注册账号 → 查看API Key→ \n"
            "⚠️ 注意：若你点击链接后跳转到其他域名（如 scan.quark.cn 或 open.quark.com），\n"
            "说明该链接已失效 —— 请直接在浏览器地址栏手动输入 https://scan.quark.cn/business\n"
            "（这是当前唯一有效的官方入口）。\n\n"
            "获取密钥后，在终端执行：\n"
            "  export SCAN_WEBSERVICE_KEY=\"your_key_here\"\n"
            "然后重新运行 OCR 命令即可。"
        )
        logger.error(error_msg)
        raise ValueError(error_msg)

class QuarkOCRClient:
    """夸克 OCR 客户端，提供图片识别功能"""

    def __init__(self, api_key: str, service_option: str, input_configs: str,
                 output_configs: str, data_type: str):
        """
        初始化 OCR 客户端

        Args:
            api_key: API 密钥
            service_option: 服务选项
            input_configs: 输入配置（JSON 字符串）
            output_configs: 输出配置（JSON 字符串）
            data_type: 数据类型（image 或 pdf）
        """
        self.api_key = api_key
        self.service_option = service_option
        self.input_configs = input_configs
        self.output_configs = output_configs
        self.data_type = data_type
        self.session = requests.Session()
        logger.info(f"QuarkOCRClient initialized with service_option={service_option}, data_type={data_type}")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def recognize(self, image_url: str = None, image_path: str = None, base64_data: str = None) -> OCRResult:
        """
        识别图片内容

        Args:
            image_url: 公网图片 URL
            image_path: 本地文件路径（自动转 BASE64）
            base64_data: base64 字符串

        Returns:
            OCRResult: 识别结果
        """
        # 验证参数：确保只有一个参数被传入
        provided_params = sum(param is not None for param in [image_url, image_path, base64_data])
        if provided_params != 1:
            logger.error(f"Invalid input: exactly one of image_url, image_path, or base64_data must be provided, got {provided_params}")
            return OCRResult(
                code=ERR_INVALID_INPUT,
                message="Exactly one of image_url, image_path, or base64_data must be provided",
                data=None
            )

        if base64_data:
            return self._recognize_base64(base64_data)
        elif image_path:
            return self._recognize_local_file(image_path)
        else:
            is_valid, error_msg = URLValidator.validate(image_url)
            if not is_valid:
                logger.error(f"URL validation failed: {error_msg}")
                return OCRResult(code=ERR_URL_VALIDATION, message=f"URL validation failed: {error_msg}", data=None)
            param = self._build_request_param(image_url=image_url)
            response = self._send_request(param)
            return self._parse_response(response)

    def _recognize_base64(self, base64_data: str) -> OCRResult:
        """
        处理 base64 字符串，支持两种格式：
        1. 纯 BASE64 字符串：/9j/4AAQSkZJRg...
        2. Data URL 格式：data:image/jpeg;base64,/9j/4AAQSkZJRg...

        Args:
            base64_data: base64 字符串

        Returns:
            OCRResult: 识别结果
        """
        base64_content = base64_data.strip()

        # 检查是否是 Data URL 格式
        if base64_content.startswith('data:'):
            try:
                if ';base64,' in base64_content:
                    base64_content = base64_content.split(';base64,', 1)[1]
                else:
                    logger.error("Invalid Data URL format: missing ';base64,' separator")
                    return OCRResult(
                        code=ERR_BASE64_FORMAT,
                        message="Invalid Data URL format, expected format: data:image/jpeg;base64,<base64_string>",
                        data=None
                    )
            except (ValueError, IndexError) as e:
                logger.error(f"Failed to parse Data URL: {str(e)}")
                return OCRResult(
                    code=ERR_BASE64_PARSE,
                    message=f"Failed to parse Data URL: {str(e)}",
                    data=None
                )

        # 验证 base64 格式
        try:
            base64.b64decode(base64_content)
        except (ValueError, binascii.Error) as e:
            logger.error(f"Invalid base64 string: {str(e)}")
            return OCRResult(code=ERR_BASE64_DECODE, message=f"Invalid base64 string: {str(e)}", data=None)

        # 使用 base64 方式调用 OCR
        param = self._build_request_param(base64_data=base64_content)
        response = self._send_request(param)
        return self._parse_response(response)

    def _recognize_local_file(self, file_path: str) -> OCRResult:
        """
        处理本地文件：读取文件并转为 BASE64 后调用 OCR

        Args:
            file_path: 本地文件路径

        Returns:
            OCRResult: 识别结果
        """
        file_path = os.path.expanduser(file_path.strip())

        # 验证文件
        is_valid, error_msg = self._validate_local_file(file_path)
        if not is_valid:
            logger.error(f"File validation failed: {error_msg}")
            return OCRResult(code=ERR_FILE_ERROR, message=f"File validation failed: {error_msg}", data=None)

        # 读取文件并转为 base64
        try:
            with open(file_path, 'rb') as f:
                file_content = f.read()
            base64_content = base64.b64encode(file_content).decode('utf-8')
        except (IOError, OSError) as e:
            logger.error(f"Failed to read file {file_path}: {str(e)}")
            return OCRResult(code=ERR_FILE_READ, message=f"Failed to read file: {str(e)}", data=None)

        # 使用 dataBase64 参数调用 OCR
        param = self._build_request_param(base64_data=base64_content)
        response = self._send_request(param)
        return self._parse_response(response)

    def _validate_local_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        if not file_path or not isinstance(file_path, str):
            return False, "File path cannot be empty"

        file_path = os.path.expanduser(file_path.strip())

        if not os.path.exists(file_path):
            return False, f"File not found: {file_path}"

        if not os.path.isfile(file_path):
            return False, f"Not a file: {file_path}"

        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            return False, f"File size exceeds {MAX_FILE_SIZE / 1024 / 1024}MB limit"

        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return False, f"File extension '{ext}' not allowed"

        return True, None

    def _build_request_param(self, image_url: str = None, base64_data: str = None) -> Dict[str, Any]:
        """
        构建请求参数，严格按照 SKILL.md 中的格式
        注意：inputConfigs 和 outputConfigs 必须是 JSON 字符串（带引号）
        """
        param = {
            "aiApiKey": self.api_key,
            "dataType": self.data_type,
            "serviceOption": self.service_option,
            "inputConfigs": self.input_configs,
            "outputConfigs": self.output_configs
        }

        # 根据输入类型选择使用 dataUrl 或 dataBase64（互斥）
        if base64_data:
            param["dataBase64"] = base64_data
        else:
            param["dataUrl"] = image_url

        return param

    def _send_request(self, param: Dict[str, Any]) -> requests.Response:
        """
        发送 HTTP 请求到 OCR API

        Args:
            param: 请求参数

        Returns:
            requests.Response: HTTP 响应对象
        """
        headers = {"Content-Type": "application/json"}

        # 带重试机制的请求发送
        for retry in range(MAX_RETRY_TIMES):
            try:
                response = self.session.post(
                    API_URL,
                    json=param,
                    headers=headers,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                return response
            except Timeout as e:
                if retry < MAX_RETRY_TIMES - 1:
                    logger.warning(f"Request timeout, retrying ({retry + 1}/{MAX_RETRY_TIMES})...")
                    continue
                logger.error(f"Request timeout after {MAX_RETRY_TIMES} retries")
                raise
            except RequestException as e:
                if retry < MAX_RETRY_TIMES - 1:
                    logger.warning(f"Request failed, retrying ({retry + 1}/{MAX_RETRY_TIMES}): {str(e)}")
                    continue
                logger.error(f"Request failed after {MAX_RETRY_TIMES} retries: {str(e)}")
                raise

    def _parse_response(self, response: requests.Response) -> OCRResult:
        """
        解析 API 响应

        Args:
            response: HTTP 响应对象

        Returns:
            OCRResult: 解析后的识别结果
        """
        if response.status_code != 200:
            error_msg = response.text[:200] if response.text else "No error message"
            logger.error(f"HTTP error {response.status_code}: {error_msg}")
            return OCRResult(
                code=ERR_HTTP_ERROR,
                message=f"HTTP {response.status_code}: {error_msg}",
                data=None
            )

        try:
            body = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            return OCRResult(
                code=ERR_JSON_PARSE,
                message=f"Failed to parse JSON: {str(e)}",
                data=None
            )

        # 直接返回 API 的原始响应
        code = body.get("code", "unknown")
        message = body.get("message")
        data = body.get("data")

        # 特殊处理 A0211 错误码（配额/余额不足）- 直接输出纯文本，不返回 JSON
        if code == "A0211":
            message = ERR_MSG_A0211_QUOTA_INSUFFICIENT

        if code == SUCCESS_CODE:
            logger.info(f"OCR recognition successful")
        else:
            logger.warning(f"OCR recognition failed with code: {code}, message: {message}")

        return OCRResult(code=code, message=message, data=data)

def _validate_json_config(config_str: str, config_name: str) -> None:
    """
    验证 JSON 配置格式

    Args:
        config_str: JSON 字符串
        config_name: 配置名称（用于错误提示）

    Raises:
        ValueError: JSON 格式错误时抛出
    """
    try:
        json.loads(config_str)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid {config_name} JSON: {str(e)}")

def main():
    """主函数，处理命令行参数并执行 OCR 识别"""
    parser = argparse.ArgumentParser(
        description="Quark OCR - 支持图片 URL、本地路径（自动转 BASE64）、BASE64 字符串",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  # 通用 OCR（URL）
  python3 scan.py \\
    --url "https://example.com/image.jpg" \\
    --service-option "structure" \\
    --input-configs '{"function_option": "RecognizeGeneralDocument"}' \\
    --output-configs '{"need_return_image": "True"}' \\
    --data-type "image"
  
  # 身份证识别（本地文件）
  python3 scan.py \\
    --path "/path/to/idcard.jpg" \\
    --service-option "structure" \\
    --input-configs '{"function_option": "RecognizeIDCard"}' \\
    --output-configs '{"need_return_image": "True"}' \\
    --data-type "image"
  
  # 文件扫描（BASE64）
  python3 scan.py \\
    --base64 "iVBORw0KGgo..." \\
    --service-option "scan" \\
    --input-configs '{"function_option": "work_scene"}' \\
    --output-configs '{"need_return_image": "True"}' \\
    --data-type "image"
        """
    )

    # 图片输入参数（三选一，必需）
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--url", "-u", help="图片 URL（如：https://example.com/image.jpg）")
    group.add_argument("--path", "-p", help="本地图片文件路径（自动转 BASE64）")
    group.add_argument("--base64", "-b", help="BASE64 字符串，支持纯 BASE64 或 Data URL 格式（如：data:image/jpeg;base64,/9j/...）")

    # API 参数（必需）
    parser.add_argument(
        "--service-option",
        required=True,
        help='serviceOption 参数（如：structure, ocr, scan）'
    )
    parser.add_argument(
        "--input-configs",
        required=True,
        help='inputConfigs JSON 字符串（如：\'{"function_option": "RecognizeGeneralDocument"}\'）'
    )
    parser.add_argument(
        "--output-configs",
        required=True,
        help='outputConfigs JSON 字符串（如：\'{"need_return_image": "True"}\'）'
    )
    parser.add_argument(
        "--data-type",
        required=True,
        choices=["image", "pdf"],
        help="数据类型（image 或 pdf）"
    )

    args = parser.parse_args()

    # 验证 JSON 参数格式
    try:
        _validate_json_config(args.input_configs, "input-configs")
        _validate_json_config(args.output_configs, "output-configs")
    except ValueError as e:
        logger.error(str(e))
        print(OCRResult(code=ERR_INVALID_JSON, message=str(e), data=None).to_json())
        sys.exit(1)

    try:
        api_key = CredentialManager.load()
        with QuarkOCRClient(
            api_key=api_key,
            service_option=args.service_option,
            input_configs=args.input_configs,
            output_configs=args.output_configs,
            data_type=args.data_type
        ) as client:
            if args.base64:
                result = client.recognize(base64_data=args.base64)
            elif args.url:
                result = client.recognize(image_url=args.url)
            else:
                result = client.recognize(image_path=args.path)

        # 输出识别结果
        print(result.to_json())
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        print(OCRResult(code=ERR_CONFIG_ERROR, message=str(e), data=None).to_json())
        sys.exit(1)
    except Timeout as e:
        logger.error(f"Request timeout: {str(e)}")
        print(OCRResult(code=ERR_TIMEOUT, message="Request timed out", data=None).to_json())
        sys.exit(1)
    except ConnectionError as e:
        logger.error(f"Network error: {str(e)}")
        print(OCRResult(code=ERR_NETWORK_ERROR, message=f"Network failed: {str(e)}", data=None).to_json())
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        print(OCRResult(code=ERR_UNKNOWN_ERROR, message=f"Unexpected error: {str(e)}", data=None).to_json())
        sys.exit(1)

if __name__ == "__main__":
    main()