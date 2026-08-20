"""
快速深度学习脱敏器 - 高性能版
Fast Deep Learning Desensitizer

针对大图片优化，使用轻量级模型和降采样策略
优先处理速度而非精度
"""

import numpy as np
from typing import Optional, List, Tuple
import logging
from PIL import Image

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FastDeepLearningDesensitizer:
    """高性能脱敏器 - 针对大图片优化"""
    
    def __init__(self, downscale_ratio: float = 0.5, 
                 max_image_size: int = 1920):
        """
        初始化快速脱敏器
        
        Args:
            downscale_ratio: 降采样比例（0-1），越小越快
            max_image_size: 最大图像尺寸，超过则自动降采样
        """
        self.downscale_ratio = downscale_ratio
        self.max_image_size = max_image_size
        self.ocr_reader = None
        self.face_detector = None
        self._use_opencv = False
        self._initialized = False
        
        self._initialize()
    
    def _initialize(self) -> None:
        """初始化轻量级组件"""
        try:
            # 初始化轻量级OCR
            self._init_fast_ocr()
            
            # 初始化轻量级人脸检测
            self._init_fast_face_detector()
            
            self._initialized = True
            logger.info("✓ FastDeepLearningDesensitizer 初始化成功")
            logger.info(f"  - 降采样比例: {self.downscale_ratio}")
            logger.info(f"  - 最大图像尺寸: {self.max_image_size}px")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    def _init_fast_ocr(self) -> None:
        """初始化快速OCR"""
        try:
            from paddleocr import PaddleOCR
            # 使用轻量配置
            self.ocr_reader = PaddleOCR(
                use_angle_cls=True, 
                lang='ch', 
                use_gpu=False,
                show_log=False,
                rec_batch_num=16  # 批量处理加速
            )
            logger.info("✓ PaddleOCR 初始化成功")
        except ImportError:
            logger.warning("PaddleOCR 未安装，尝试 EasyOCR...")
            try:
                import easyocr
                self.ocr_reader = easyocr.Reader(
                    ['ch_sim', 'en'],
                    gpu=False,
                    verbose=False
                )
                logger.info("✓ EasyOCR 初始化成功")
            except ImportError:
                logger.warning("OCR库都未安装，将使用简单文字检测")
                self.ocr_reader = None
        except Exception as e:
            logger.warning(f"PaddleOCR 初始化失败: {e}")
            self.ocr_reader = None
    
    def _init_fast_face_detector(self) -> None:
        """初始化快速人脸检测"""
        # 优先尝试OpenCV
        try:
            import cv2
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_alt_tree.xml'
            self.face_detector = cv2.CascadeClassifier(cascade_path)
            
            if not self.face_detector.empty():
                self._use_opencv = True
                logger.info("✓ 快速人脸检测器 初始化成功")
                return
        except Exception:
            pass
        
        # 回退到Pillow模式
        self._use_opencv = False
        self.face_detector = None
        logger.info("✓ 使用快速模式（简化人脸检测）")
    
    def desensitize(self, image_data: bytes,
                    desensitize_text: bool = True,
                    desensitize_face: bool = True,
                    blur_strength: int = 31) -> bytes:
        """
        快速脱敏处理
        
        Args:
            image_data: 原始图像字节数据
            desensitize_text: 是否脱敏文字
            desensitize_face: 是否脱敏人脸
            blur_strength: 模糊强度
            
        Returns:
            脱敏后的图像字节数据
        """
        import io
        from PIL import Image
        
        try:
            # 解码图像
            img = Image.open(io.BytesIO(image_data))
            orig_w, orig_h = img.size
            
            # 降采样处理大图
            scale = 1.0
            if max(orig_h, orig_w) > self.max_image_size:
                scale = self.max_image_size / max(orig_h, orig_w)
                new_w = int(orig_w * scale)
                new_h = int(orig_h * scale)
                img = img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            
            # 脱敏处理
            if desensitize_text and self.ocr_reader:
                img = self._fast_detect_and_blur_text(img, blur_strength)
            
            if desensitize_face:
                img = self._fast_face_blur(img, blur_strength)
            
            # 恢复原始尺寸
            if scale < 1.0:
                img = img.resize((orig_w, orig_h), Image.Resampling.LANCZOS)
            
            # 编码回字节
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=90)
            return output.getvalue()
            
        except ImportError as e:
            logger.error(f"缺少依赖库: {e}")
            return image_data
        except Exception as e:
            logger.error(f"快速脱敏失败: {e}")
            return image_data
    
    def _fast_detect_and_blur_text(self, img: Image.Image, blur_strength: int) -> Image.Image:
        """
        快速文字检测和模糊
        """
        try:
            from PIL import ImageFilter
            
            if self.ocr_reader is None:
                return img
            
            # PaddleOCR
            if hasattr(self.ocr_reader, 'ocr'):
                results = self.ocr_reader.ocr(np.array(img), cls=True)
                
                if not results or not results[0]:
                    return img
                
                img = img.copy()
                
                for line in results[0]:
                    box = line[0]
                    x_min = int(min(p[0] for p in box))
                    x_max = int(max(p[0] for p in box))
                    y_min = int(min(p[1] for p in box))
                    y_max = int(max(p[1] for p in box))
                    
                    # 过滤太小的区域
                    if (x_max - x_min) < 10 or (y_max - y_min) < 5:
                        continue
                    
                    # 添加padding
                    padding = 3
                    x_min = max(0, x_min - padding)
                    x_max = min(img.width, x_max + padding)
                    y_min = max(0, y_min - padding)
                    y_max = min(img.height, y_max + padding)
                    
                    if x_max > x_min and y_max > y_min:
                        region = img.crop((x_min, y_min, x_max, y_max))
                        blurred = region.filter(ImageFilter.GaussianBlur(radius=blur_strength//8))
                        img.paste(blurred, (x_min, y_min))
                
                return img
            
            # EasyOCR
            elif hasattr(self.ocr_reader, 'detectText'):
                results = self.ocr_reader.detectText(np.array(img))
                
                if not results or len(results) == 0:
                    return img
                
                img = img.copy()
                
                for box_group in results:
                    for box in box_group:
                        x_min, x_max, y_min, y_max = map(int, box)
                        
                        if (x_max - x_min) < 10 or (y_max - y_min) < 5:
                            continue
                        
                        padding = 3
                        x_min = max(0, x_min - padding)
                        x_max = min(img.width, x_max + padding)
                        y_min = max(0, y_min - padding)
                        y_max = min(img.height, y_max + padding)
                        
                        if x_max > x_min and y_max > y_min:
                            region = img.crop((x_min, y_min, x_max, y_max))
                            blurred = region.filter(ImageFilter.GaussianBlur(radius=blur_strength//8))
                            img.paste(blurred, (x_min, y_min))
                
                return img
            
            return img
            
        except Exception as e:
            logger.warning(f"文字检测失败: {e}")
            return img
    
    def _fast_face_blur(self, img: Image.Image, blur_strength: int) -> Image.Image:
        """
        快速人脸模糊
        """
        try:
            from PIL import ImageFilter
            
            if self._use_opencv and self.face_detector is not None:
                import cv2
                img_cv = np.array(img)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
                
                # 使用更快的检测参数
                faces = self.face_detector.detectMultiScale(
                    gray,
                    scaleFactor=1.2,
                    minNeighbors=3,
                    minSize=(40, 40)
                )
                
                if len(faces) > 0:
                    img = img.copy()
                    
                    for (x, y, w, h) in faces:
                        padding_x = int(w * 0.05)
                        padding_y = int(h * 0.05)
                        
                        x1 = max(0, x - padding_x)
                        y1 = max(0, y - padding_y)
                        x2 = min(img.width, x + w + padding_x)
                        y2 = min(img.height, y + h + padding_y)
                        
                        if x2 > x1 and y2 > y1:
                            region = img.crop((x1, y1, x2, y2))
                            blurred = region.filter(ImageFilter.GaussianBlur(radius=blur_strength//8))
                            img.paste(blurred, (x1, y1))
                
                return img
            
            # 无OpenCV时跳过或使用简化检测
            return img
            
        except Exception as e:
            logger.warning(f"人脸检测失败: {e}")
            return img
    
    def get_supported_features(self) -> List[str]:
        """获取支持的脱敏功能"""
        features = ["高性能模式"]
        if self.ocr_reader:
            features.append("文字检测(OCR)")
        else:
            features.append("文字检测(简单)")
        if self._use_opencv:
            features.append("人脸检测(OpenCV)")
        else:
            features.append("人脸检测(基础)")
        return features


def create_desensitizer() -> FastDeepLearningDesensitizer:
    """工厂函数：创建快速脱敏器实例"""
    return FastDeepLearningDesensitizer()


if __name__ == "__main__":
    # 测试代码
    print("正在初始化 FastDeepLearningDesensitizer...")
    desensitizer = FastDeepLearningDesensitizer()
    print(f"支持的脱敏功能: {desensitizer.get_supported_features()}")
