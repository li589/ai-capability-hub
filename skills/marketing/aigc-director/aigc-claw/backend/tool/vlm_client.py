import os
from typing import List, Optional
from config import Config

try:
    from tool.vlm_dashscope import QwenVLClient
    from tool.vlm_gemini import GeminiVLClient
except ImportError:
    from vlm_dashscope import QwenVLClient
    from vlm_gemini import GeminiVLClient

class VLM:
    def __init__(self,
                 dashscope_api_key: Optional[str] = None,
                 dashscope_base_url: Optional[str] = None,
                 gemini_api_key: Optional[str] = None,
                 gemini_base_url: Optional[str] = None,
                 local_proxy: Optional[str] = None):
        """
        Unified VLM (Vision Language Model) Client
        Routes requests to DashScope (QwenVL) or Gemini based on model name.
        """
        # Initialize DashScope Client
        self.dashscope_client = QwenVLClient(
            api_key=dashscope_api_key,
            base_url=dashscope_base_url
        )
        # Initialize Gemini Client
        self.gemini_client = GeminiVLClient(
            api_key=gemini_api_key,
            base_url=gemini_base_url
        )

    def query(self,
             prompt: str,
             image_paths: Optional[List[str]] = None,
             model: str = "qwen3.5-plus",
             session_id: Optional[str] = None) -> str:
        if Config.PRINT_MODEL_INPUT:
            print("---- VLM REQUEST ----")
            print(f"Prompt: {prompt}")
            if image_paths:
                print(f"Images: {len(image_paths)}")
                for p in image_paths:
                    if p.startswith("data:"):
                        print(f" - [Base64图片]")
                    else:
                        print(f" - {p}")
            print(f"Model: {model}")
            if session_id:
                print(f"Session ID: {session_id}")
            print("-" * 30)

        # Determine backend provider
        model_lower = model.lower()
        is_gemini = "gemini" in model_lower

        if is_gemini:
            # 处理图片路径
            processed_images = []
            for p in image_paths or []:
                if p.startswith("data:") or p.startswith("http") or p.startswith("file://"):
                    processed_images.append(p)
                else:
                    processed_images.append(p)  # 传递原始路径，内部会处理
            return self.gemini_client.chat(text=prompt, images=processed_images, model=model)
        else:
            # Qwen (DashScope) - 需要将 base64 保存为临时文件
            file_urls = []
            import tempfile
            import base64 as b64

            for p in image_paths or []:
                if p.startswith("data:"):
                    # Base64 数据 URL，需要解码并保存为临时文件
                    try:
                        # 解析 data URL: data:image/png;base64,xxxxx
                        header, b64_data = p.split(",", 1)
                        mime_type = header.split(";")[0].replace("data:", "")
                        image_data = b64.b64decode(b64_data)

                        # 创建临时文件
                        suffix = f".{mime_type.split('/')[-1]}" if '/' in mime_type else ".png"
                        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                            tmp.write(image_data)
                            temp_path = tmp.name

                        abs_path = os.path.abspath(temp_path)
                        file_urls.append(f"file://{abs_path}")
                    except Exception as e:
                        print(f"Error processing base64 image: {e}")
                        raise ValueError(f"无法解析 base64 图片: {e}")
                elif p.startswith("http") or p.startswith("file://"):
                    file_urls.append(p)
                else:
                    abs_path = os.path.abspath(p)
                    file_urls.append(f"file://{abs_path}")
            return self.dashscope_client.chat(text=prompt, images=file_urls, model=model, stream=False)