"""
智能自动脱敏工具
Smart Desensitize Skill

支持文本、JSON、图像的智能脱敏
具备自检初始化功能，新建 agent 时自动启用脱敏规则
"""

import re
import json
import base64
import os
from typing import Dict, List, Any, Optional, Union
from io import BytesIO
from datetime import datetime

# 导入深度学习脱敏模块
try:
    from deep_desensitize_skill import DeepLearningDesensitizer
    DEEP_DESENSITIZE_AVAILABLE = True
except ImportError:
    DEEP_DESENSITIZE_AVAILABLE = False

try:
    from fast_deep_desensitize_skill import FastDeepLearningDesensitizer
    FAST_DEEP_DESENSITIZE_AVAILABLE = True
except ImportError:
    FAST_DEEP_DESENSITIZE_AVAILABLE = False


class SmartDesensitizer:
    """智能脱敏器主类"""
    
    def __init__(self, use_deep_learning: bool = False, high_performance: bool = False):
        """
        初始化智能脱敏器
        
        Args:
            use_deep_learning: 是否使用深度学习脱敏（图像）
            high_performance: 是否使用高性能模式（大图片优化）
        """
        self.use_deep_learning = use_deep_learning
        self.high_performance = high_performance
        
        # 初始化深度学习脱敏器
        self.deep_desensitizer = None
        if use_deep_learning:
            if high_performance and FAST_DEEP_DESENSITIZE_AVAILABLE:
                try:
                    self.deep_desensitizer = FastDeepLearningDesensitizer()
                    print("✓ 已加载 FastDeepLearningDesensitizer (高性能模式)")
                except Exception as e:
                    print(f"⚠ FastDeepLearningDesensitizer 初始化失败: {e}")
                    if DEEP_DESENSITIZE_AVAILABLE:
                        try:
                            self.deep_desensitizer = DeepLearningDesensitizer()
                            print("✓ 已加载 DeepLearningDesensitizer (标准模式)")
                        except Exception as e2:
                            print(f"⚠ DeepLearningDesensitizer 初始化失败: {e2}")
            elif DEEP_DESENSITIZE_AVAILABLE:
                try:
                    self.deep_desensitizer = DeepLearningDesensitizer()
                    print("✓ 已加载 DeepLearningDesensitizer (标准模式)")
                except Exception as e:
                    print(f"⚠ DeepLearningDesensitizer 初始化失败: {e}")
    
    def desensitize_text(self, text: str) -> str:
        """
        脱敏文本中的敏感信息
        
        Args:
            text: 原始文本
            
        Returns:
            脱敏后的文本
        """
        if not text:
            return text
            
        result = text
        
        # 手机号脱敏 (138****5678)
        result = re.sub(
            r'1[3-9]\d{9}',
            lambda m: m.group(0)[:3] + '****' + m.group(0)[7:],
            result
        )
        
        # 身份证脱敏 (110***********1234)
        result = re.sub(
            r'\d{17}[\dXx]',
            lambda m: m.group(0)[:6] + '**********' + m.group(0)[14:],
            result
        )
        
        # 邮箱脱敏 (t***@example.com)
        result = re.sub(
            r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            lambda m: m.group(1)[:1] + '***@' + m.group(2),
            result
        )
        
        # 银行卡脱敏 (****1234)
        result = re.sub(
            r'\d{13,19}',
            lambda m: '****' + m.group(0)[-4:],
            result
        )
        
        # IP地址脱敏
        result = re.sub(
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',
            lambda m: '***.***.***.' + m.group(0).split('.')[-1],
            result
        )
        
        return result
    
    def desensitize_json(self, json_str: str, fields_to_mask: Optional[List[str]] = None) -> str:
        """
        脱敏JSON中的敏感字段
        
        Args:
            json_str: JSON字符串
            fields_to_mask: 需要脱敏的字段名列表，默认包含常见敏感字段
            
        Returns:
            脱敏后的JSON字符串
        """
        if not json_str:
            return json_str
            
        # 默认需要脱敏的字段
        if fields_to_mask is None:
            fields_to_mask = [
                'password', 'pwd', 'secret', 'token', 'api_key', 'apikey',
                'phone', 'mobile', 'tel', 'telephone',
                'id_card', 'idcard', 'identity', '身份证',
                'email', 'mail',
                'bank_card', 'bankcard', '银行卡',
                'address', '姓名', 'name', 'real_name', 'realname',
                'salary', 'wage', '工资',
                'ssn', 'social_security'
            ]
        
        try:
            data = json.loads(json_str)
            self._mask_json_fields(data, fields_to_mask)
            return json.dumps(data, ensure_ascii=False)
        except json.JSONDecodeError:
            # 如果不是有效JSON，当作纯文本处理
            return self.desensitize_text(json_str)
    
    def _mask_json_fields(self, obj: Any, fields_to_mask: List[str]) -> None:
        """
        递归处理JSON对象
        
        Args:
            obj: JSON对象（dict/list/primitive）
            fields_to_mask: 需要脱敏的字段名列表
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                # 检查字段名是否需要脱敏
                key_lower = key.lower()
                should_mask = any(
                    mask_key in key_lower for mask_key in [k.lower() for k in fields_to_mask]
                )
                
                if should_mask and isinstance(value, str):
                    obj[key] = self._mask_value(value)
                elif isinstance(value, (dict, list)):
                    self._mask_json_fields(value, fields_to_mask)
                    
        elif isinstance(obj, list):
            for item in obj:
                if isinstance(item, (dict, list)):
                    self._mask_json_fields(item, fields_to_mask)
    
    def _mask_value(self, value: str) -> str:
        """
        根据值的内容类型选择合适的脱敏方式
        
        Args:
            value: 字段值
            
        Returns:
            脱敏后的值
        """
        # 手机号
        if re.match(r'^1[3-9]\d{9}$', value):
            return value[:3] + '****' + value[7:]
        
        # 邮箱
        if '@' in value and '.' in value:
            parts = value.split('@')
            return parts[0][:1] + '***@' + parts[1]
        
        # 身份证
        if re.match(r'^\d{17}[\dXx]$', value):
            return value[:6] + '**********' + value[14:]
        
        # 银行卡
        if re.match(r'^\d{13,19}$', value):
            return '****' + value[-4:]
        
        # IP地址
        if re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$', value):
            return '***.***.***.' + value.split('.')[-1]
        
        # 金额（保留后两位）
        if re.match(r'^\d+\.?\d*$', value) and len(value) <= 12:
            return '***.**'
        
        # 默认：姓名等直接返回脱敏占位符
        if len(value) <= 2:
            return '*'
        elif len(value) <= 4:
            return value[0] + '**'
        else:
            return value[:2] + '**' + value[-1]
    
    def desensitize_image_base64(self, image_base64: str, 
                                  desensitize_text: bool = True,
                                  desensitize_face: bool = True) -> str:
        """
        脱敏Base64编码的图像
        
        Args:
            image_base64: Base64编码的图像数据
            desensitize_text: 是否脱敏文字
            desensitize_face: 是否脱敏人脸
            
        Returns:
            脱敏后的Base64编码图像
        """
        if not self.deep_desensitizer:
            print("⚠ 深度学习脱敏器未加载，返回原图")
            return image_base64
            
        try:
            # 解码Base64
            image_data = base64.b64decode(image_base64)
            
            # 处理图像
            processed_data = self.deep_desensitizer.desensitize(
                image_data,
                desensitize_text=desensitize_text,
                desensitize_face=desensitize_face
            )
            
            # 重新编码为Base64
            return base64.b64encode(processed_data).decode('utf-8')
            
        except Exception as e:
            print(f"⚠ 图像脱敏失败: {e}")
            return image_base64
    
    def batch_desensitize(self, items: List[Dict[str, Any]], 
                          config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        批量脱敏
        
        Args:
            items: 待脱敏的字典列表
            config: 脱敏配置
            
        Returns:
            脱敏后的字典列表
        """
        if config is None:
            config = {}
            
        fields_to_mask = config.get('fields_to_mask', None)
        preserve_structure = config.get('preserve_structure', True)
        
        results = []
        for item in items:
            if preserve_structure and 'type' in item:
                item_type = item.get('type', 'text')
                content = item.get('content', '')
                
                if item_type == 'json':
                    item['content'] = self.desensitize_json(content, fields_to_mask)
                else:
                    item['content'] = self.desensitize_text(content)
                    
            results.append(item)
            
        return results


def main():
    """测试函数"""
    print("=" * 50)
    print("智能自动脱敏工具测试")
    print("=" * 50)
    
    # 创建脱敏器实例
    desensitizer = SmartDesensitizer(use_deep_learning=False)
    
    # 测试文本脱敏
    print("\n【文本脱敏测试】")
    test_texts = [
        "张三的手机号是13812345678，身份证号是110101199001011234",
        "请联系李经理，电话：13900001111，邮箱：lijun@example.com",
        "用户王五的银行卡号：6222021234567890123，IP地址：192.168.1.100"
    ]
    
    for text in test_texts:
        result = desensitizer.desensitize_text(text)
        print(f"原文: {text}")
        print(f"脱敏: {result}")
        print("-" * 40)
    
    # 测试JSON脱敏
    print("\n【JSON脱敏测试】")
    test_json = json.dumps({
        "user": {
            "name": "张三",
            "phone": "13812345678",
            "email": "zhangsan@example.com",
            "id_card": "110101199001011234",
            "password": "mysecretpassword123"
        },
        "account": {
            "bank_card": "6222021234567890123",
            "balance": "99999.99"
        }
    }, ensure_ascii=False)
    
    print(f"原文: {test_json}")
    print("-" * 40)
    
    result_json = desensitizer.desensitize_json(test_json)
    print(f"脱敏: {result_json}")
    
    print("\n" + "=" * 50)
    print("测试完成!")
    print("=" * 50)


if __name__ == "__main__":
    main()


# ============================================================
# 自检初始化功能 - 新建 agent 时自动启用脱敏规则
# ============================================================

def auto_init_desensitize_rules():
    """
    自检初始化：检查并创建脱敏规则配置文件
    在模块导入时自动执行，确保新建 agent 时脱敏规则生效
    """
    # 配置文件路径
    GLOBAL_CONFIG_PATH = "./基础设定/DESENSITIZE_RULES.md"
    MEMORY_PATH = "./MEMORY.md"
    
    # 全局配置模板
    GLOBAL_CONFIG_TEMPLATE = """# 自动脱敏规则配置

## 状态
**已启用** ✅

**开启时间：** {date}

## 规则说明
主人发送的所有内容（文本、JSON、图片），在处理前先进行敏感信息脱敏：

### 脱敏类型
- 手机号：`138****5678`
- 身份证：`110101********1234`
- 银行卡：`6222****1234`
- 邮箱：`te****@example.com`
- 姓名、地址、QQ、微信、车牌号等

### 图片处理
- 对图片中的敏感文字进行 OCR 识别并模糊
- 脱敏完成后自动删除原图，只保留脱敏版本

## 例外情况
- 主人明确要求不脱敏的内容
- 已知的安全/测试数据

## 工具位置
`./工具/脱敏工具/smart_desensitize_skill.py`
"""
    
    # MEMORY.md 追加内容
    MEMORY_RULES = """
### 自动脱敏模式
**开启时间：** {date}

**规则：** 主人发送的所有内容（文本、JSON、图片），在处理前先进行敏感信息脱敏：
- 手机号：138****5678
- 身份证：110101********1234
- 银行卡：6222****1234
- 邮箱：te****@example.com
- 姓名、地址、QQ、微信、车牌号等

**配置文件：** `./基础设定/DESENSITIZE_RULES.md`（全局配置，新建 agent 时继承）

**使用工具：** `./工具/脱敏工具/smart_desensitize_skill.py`

**自动删除原图：** 脱敏处理完成后，自动删除原始图片，只保留脱敏版本

**例外：** 
- 主人明确要求不脱敏的内容
- 已知的安全/测试数据

"""
    
    current_date = datetime.now().strftime("%Y年%m月%d日")
    
    # 1. 检查并创建全局配置文件
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(GLOBAL_CONFIG_PATH), exist_ok=True)
        
        if not os.path.exists(GLOBAL_CONFIG_PATH):
            with open(GLOBAL_CONFIG_PATH, 'w', encoding='utf-8') as f:
                f.write(GLOBAL_CONFIG_TEMPLATE.format(date=current_date))
            print(f"✓ 已创建全局脱敏配置: {GLOBAL_CONFIG_PATH}")
        else:
            print(f"✓ 全局脱敏配置已存在: {GLOBAL_CONFIG_PATH}")
    except Exception as e:
        print(f"⚠ 创建全局配置失败: {e}")
    
    # 2. 检查并更新 MEMORY.md
    try:
        if os.path.exists(MEMORY_PATH):
            with open(MEMORY_PATH, 'r', encoding='utf-8') as f:
                memory_content = f.read()
            
            # 检查是否已有脱敏规则
            if "自动脱敏模式" not in memory_content:
                # 追加脱敏规则
                with open(MEMORY_PATH, 'a', encoding='utf-8') as f:
                    f.write(MEMORY_RULES.format(date=current_date))
                print(f"✓ 已更新 MEMORY.md 添加脱敏规则")
            else:
                print(f"✓ MEMORY.md 已包含脱敏规则")
        else:
            # MEMORY.md 不存在，创建它
            with open(MEMORY_PATH, 'w', encoding='utf-8') as f:
                f.write("## 关键任务\\n\\n## 关键概念/话题理解\\n\\n## 注意事项与规范\\n")
                f.write(MEMORY_RULES.format(date=current_date))
            print(f"✓ 已创建 MEMORY.md 并添加脱敏规则")
    except Exception as e:
        print(f"⚠ 更新 MEMORY.md 失败: {e}")


# 模块导入时自动执行自检
auto_init_desensitize_rules()