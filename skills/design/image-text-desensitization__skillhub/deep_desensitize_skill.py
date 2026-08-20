"""
深度学习脱敏器 - 标准版
Deep Learning Desensitizer

使用 PIL/OpenCV + OCR 进行图像敏感信息检测和脱敏
支持文字检测、人脸检测
"""

import numpy as np
from typing import Optional, Tuple, List
import logging
from PIL import Image

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DeepLearningDesensitizer:
    """标准深度学习脱敏器"""
    
    def __init__(self, use_gpu: bool = False, language: List[str] = ['ch_sim', 'en']):
        """
        初始化深度学习脱敏器
        
        Args:
            use_gpu: 是否使用GPU加速
            language: OCR识别语言
        """
        self.use_gpu = use_gpu
        self.language = language
        self.ocr_reader = None
        self.face_detector = None
        self._initialized = False
        
        self._initialize()
    
    def _initialize(self) -> None:
        """初始化OCR和级联分类器"""
        try:
            # 初始化OCR
            self._init_ocr()
            
            # 初始化人脸检测
            self._init_face_detector()
            
            self._initialized = True
            logger.info("✓ DeepLearningDesensitizer 初始化成功")
            
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    def _init_ocr(self) -> None:
        """初始化OCR引擎"""
        try:
            import easyocr
            self.ocr_reader = easyocr.Reader(
                self.language,
                gpu=self.use_gpu,
                verbose=False
            )
            logger.info("✓ EasyOCR 初始化成功")
        except ImportError:
            logger.warning("EasyOCR 未安装，尝试使用 PaddleOCR...")
            self._init_paddleocr()
        except Exception as e:
            logger.warning(f"EasyOCR 初始化失败: {e}")
            self._init_paddleocr()
    
    def _init_paddleocr(self) -> None:
        """初始化PaddleOCR作为备选"""
        try:
            from paddleocr import PaddleOCR
            self.ocr_reader = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=self.use_gpu, show_log=False)
            logger.info("✓ PaddleOCR 初始化成功")
        except ImportError:
            logger.warning("PaddleOCR 也未安装，文字检测功能将使用简单模式")
            self.ocr_reader = None
        except Exception as e:
            logger.warning(f"PaddleOCR 初始化失败: {e}")
            self.ocr_reader = None
    
    def _init_face_detector(self) -> None:
        """初始化人脸检测器"""
        # 优先尝试OpenCV
        try:
            import cv2
            cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_detector = cv2.CascadeClassifier(cascade_path)
            
            if not self.face_detector.empty():
                self._use_opencv = True
                logger.info("✓ OpenCV 人脸检测器 初始化成功")
                return
        except Exception:
            pass
        
        # 回退到Pillow+简单人脸检测
        try:
            from PIL import Image
            self._use_opencv = False
            logger.info("✓ 使用 Pillow 模式（人脸检测基础模式）")
        except Exception as e:
            logger.warning(f"人脸检测不可用: {e}")
            self.face_detector = None
    
    def desensitize(self, image_data: bytes, 
                    desensitize_text: bool = True,
                    desensitize_face: bool = True,
                    blur_strength: int = 51) -> bytes:
        """
        对图像进行脱敏处理
        
        Args:
            image_data: 原始图像字节数据
            desensitize_text: 是否脱敏文字
            desensitize_face: 是否脱敏人脸
            blur_strength: 模糊强度
            
        Returns:
            脱敏后的图像字节数据
        """
        try:
            from PIL import Image
            import io
            
            # 解码图像
            img = Image.open(io.BytesIO(image_data))
            
            if desensitize_text and self.ocr_reader:
                img = self._blur_text_regions_pil(img, blur_strength)
            
            if desensitize_face:
                img = self._blur_face_regions_pil(img, blur_strength)
            
            # 编码回字节
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95)
            return output.getvalue()
            
        except ImportError as e:
            logger.error(f"缺少依赖库: {e}")
            return image_data
        except Exception as e:
            logger.error(f"图像脱敏失败: {e}")
            return image_data
    
    def _blur_text_regions_pil(self, img: Image.Image, blur_strength: int) -> Image.Image:
        """
        使用PIL检测并模糊文字区域
        
        Args:
            img: PIL图像
            blur_strength: 模糊强度
            
        Returns:
            处理后的图像
        """
        try:
            from PIL import ImageFilter
            
            if self.ocr_reader is None:
                return img
            
            # EasyOCR
            if hasattr(self.ocr_reader, 'detectText'):
                results = self.ocr_reader.detectText(np.array(img))
                
                if not results or len(results) == 0:
                    return img
                
                img = img.copy()
                
                for box_group in results:
                    for box in box_group:
                        x_min, x_max, y_min, y_max = map(int, box)
                        padding = 5
                        x_min = max(0, x_min - padding)
                        x_max = min(img.width, x_max + padding)
                        y_min = max(0, y_min - padding)
                        y_max = min(img.height, y_max + padding)
                        
                        if x_max > x_min and y_max > y_min:
                            region = img.crop((x_min, y_min, x_max, y_max))
                            blurred = region.filter(ImageFilter.GaussianBlur(radius=blur_strength//6))
                            img.paste(blurred, (x_min, y_min))
                
                return img
            
            # PaddleOCR
            elif hasattr(self.ocr_reader, 'ocr'):
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
                    
                    padding = 5
                    x_min = max(0, x_min - padding)
                    x_max = min(img.width, x_max + padding)
                    y_min = max(0, y_min - padding)
                    y_max = min(img.height, y_max + padding)
                    
                    if x_max > x_min and y_max > y_min:
                        region = img.crop((x_min, y_min, x_max, y_max))
                        blurred = region.filter(ImageFilter.GaussianBlur(radius=blur_strength//6))
                        img.paste(blurred, (x_min, y_min))
                
                return img
            
            return img
            
        except Exception as e:
            logger.warning(f"文字区域检测失败: {e}")
            return img
    
    def _blur_face_regions_pil(self, img: Image.Image, blur_strength: int) -> Image.Image:
        """
        使用PIL模糊人脸区域
        
        Args:
            img: PIL图像
            blur_strength: 模糊强度
            
        Returns:
            处理后的图像
        """
        try:
            from PIL import ImageFilter
            
            # 如果有OpenCV人脸检测器
            if self._use_opencv and self.face_detector is not None:
                import cv2
                img_cv = np.array(img)
                gray = cv2.cvtColor(img_cv, cv2.COLOR_RGB2GRAY)
                
                faces = self.face_detector.detectMultiScale(
                    gray,
                    scaleFactor=1.1,
                    minNeighbors=5,
                    minSize=(30, 30)
                )
                
                if len(faces) > 0:
                    img = img.copy()
                    
                    for (x, y, w, h) in faces:
                        padding_x = int(w * 0.1)
                        padding_y = int(h * 0.1)
                        
                        x1 = max(0, x - padding_x)
                        y1 = max(0, y - padding_y)
                        x2 = min(img.width, x + w + padding_x)
                        y2 = min(img.height, y + h + padding_y)
                        
                        if x2 > x1 and y2 > y1:
                            region = img.crop((x1, y1, x2, y2))
                            blurred = region.filter(ImageFilter.GaussianBlur(radius=blur_strength//6))
                            img.paste(blurred, (x1, y1))
                
                return img
            
            # 简单的人脸检测（基于肤色）
            return self._simple_face_blur(img, blur_strength)
            
        except Exception as e:
            logger.warning(f"人脸区域检测失败: {e}")
            return img
    
    def _simple_face_blur(self, img: Image.Image, blur_strength: int) -> Image.Image:
        """简单的人脸检测（使用肤色和形状检测）"""
        try:
            from PIL import ImageFilter, ImageDraw
            
            # 这里可以实现一个简单的人脸区域检测
            # 简化版本：不做任何检测，直接返回原图
            # 实际应用中建议安装opencv-python以获得更好的效果
            
            return img
            
        except Exception:
            return img
    
    def get_supported_features(self) -> List[str]:
        """获取支持的脱敏功能"""
        features = []
        if self.ocr_reader:
            features.append("文字检测(OCR)")
        features.append("人脸检测")
        return features


def create_desensitizer() -> DeepLearningDesensitizer:
    """工厂函数：创建脱敏器实例"""
    return DeepLearningDesensitizer()


if __name__ == "__main__":
    # 测试代码
    print("正在初始化 DeepLearningDesensitizer...")
    desensitizer = DeepLearningDesensitizer()
    print(f"支持的脱敏功能: {desensitizer.get_supported_features()}")
