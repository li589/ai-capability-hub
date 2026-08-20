"""
核心工具函数

提供分词、停用词、日志、配置加载、文件编码检测等通用功能。
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, Union
import json


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """获取统一 logger"""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            "[%(asctime)s] %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
        logger.setLevel(level)
    return logger


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """加载 config.json

    Args:
        config_path: 配置文件路径，默认 <项目根>/config.json

    Returns:
        配置字典
    """
    if config_path is None:
        # 项目根目录
        config_path = Path(__file__).resolve().parent.parent / "config.json"

    if not config_path.exists():
        return {}

    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============== 中文停用词 ==============
# v2.0.0 扩充版（v1.2.0 的 stopwords + 哈工大停用词表核心）
CHINESE_STOPWORDS = {
    # 标点
    "。", "，", "！", "？", "、", "；", "：", "—", "…", "～", "·",
    "?", "!", ",", ".", ";", ":", "~", "`", "'", "\"", "(", ")", "[", "]", "{", "}",
    # 代词
    "我", "你", "他", "她", "它", "我们", "你们", "他们", "她们", "它们",
    "这", "那", "这个", "那个", "这些", "那些", "此", "其",
    "自己", "本人", "本身",
    # 助词/虚词
    "的", "了", "是", "在", "有", "和", "就", "不", "也", "都", "要", "会", "可以", "能",
    "一个", "什么", "怎么", "为什么", "吗", "呢", "吧", "啊", "哦", "嗯", "哈",
    "哈哈", "嘿嘿", "嘻嘻", "呵呵", "咯", "哒", "噢", "喔", "哇", "哎", "唉",
    # 介词/连词
    "把", "被", "给", "让", "使", "从", "向", "到", "为", "为了", "因为", "所以",
    "但是", "不过", "可是", "然而", "而且", "并且", "或者", "还是", "如果", "虽然",
    "即使", "只要", "只有", "除非", "除了",
    # 数字
    "一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "百", "千", "万",
    "一些", "所有", "全部", "每个", "任何",
    # 时间
    "今天", "昨天", "明天", "前天", "后天", "现在", "以前", "以后", "刚才", "刚刚",
    "已经", "正在", "将", "会", "可能", "应该",
    # 常见语气
    "好吧", "好的", "可以", "行", "嗯嗯", "哦哦", "啊啊", "嘿嘿嘿",
}


def is_stopword(word: str) -> bool:
    """判断是否为停用词"""
    return word in CHINESE_STOPWORDS


# ============== 文件编码自动检测 ==============
# v2.1.0 新增：Windows 导出的聊天记录常为 GBK/GB18030，
# 固定按 utf-8 读取会直接 UnicodeDecodeError，这里按优先级自动尝试。
DEFAULT_READ_ENCODINGS = ("utf-8-sig", "utf-8", "gb18030")


def decode_bytes_auto(data: bytes,
                      encodings: Tuple[str, ...] = DEFAULT_READ_ENCODINGS) -> Tuple[str, str]:
    """按优先级尝试解码字节串

    Args:
        data: 原始字节
        encodings: 依次尝试的编码列表（默认 utf-8-sig → utf-8 → gb18030）

    Returns:
        (解码后的文本, 实际使用的编码)

    Raises:
        ValueError: 所有编码都失败时抛出（含友好中文提示）
    """
    for enc in encodings:
        try:
            return data.decode(enc), enc
        except (UnicodeDecodeError, LookupError):
            continue
    raise ValueError(
        "无法识别文件编码（已尝试 %s）。" % "、".join(encodings)
        + "请将文件另存为 UTF-8 或 GBK 编码后重试。"
    )


def read_text_auto(file_path: Union[str, Path],
                   encodings: Tuple[str, ...] = DEFAULT_READ_ENCODINGS) -> Tuple[str, str]:
    """读取文本文件并自动检测编码（utf-8-sig → utf-8 → gb18030）

    Args:
        file_path: 文件路径
        encodings: 依次尝试的编码列表

    Returns:
        (文件内容, 实际使用的编码)

    Raises:
        FileNotFoundError: 文件不存在
        ValueError: 所有编码都无法解码（含友好中文提示）
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"文件不存在: {path}")
    if not path.is_file():
        raise ValueError(f"路径不是文件: {path}")
    data = path.read_bytes()
    if not data:
        return "", encodings[0]
    try:
        return decode_bytes_auto(data, encodings)
    except ValueError as e:
        raise ValueError(f"读取文件 {path} 失败：{e}")


# ============== 简易 jieba 替代品 ==============
# v2.0.0 默认使用正则分词（向后兼容）
# 如果安装了 jieba，自动切换到 jieba
def _load_custom_dict(dict_path=None) -> int:
    """加载 jieba 自定义词典，返回成功加载的词条数。

    v2.5.0：不再使用 ``jieba.load_userdict()``。官方 jieba 的
    ``load_userdict`` 按任意空白 ``split()`` 切分，而 jieba3k 按空格
    ``split(" ")`` 切分——对 TAB 分隔的词典，jieba3k 会因 ``tup[1]``
    越界抛 IndexError，导致 ``core.utils`` 在模块加载期直接崩溃。
    这里自行解析（TAB/空格均兼容、跳过 # 注释与空行、去重、容错含空格
    词条），逐条调用 ``jieba.add_word()``，对任意 jieba 变体都健壮。
    """
    if dict_path is None:
        dict_path = (
            Path(__file__).resolve().parent.parent
            / "analyzers" / "lexicon" / "jieba_dict" / "user_dict.txt"
        )
    dict_path = Path(dict_path)
    if not dict_path.exists():
        return 0

    loaded = 0
    seen = set()
    with open(dict_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()  # 任意空白（TAB/空格）均兼容
            if len(parts) < 2:
                continue
            word, freq_s = parts[0], parts[1]
            if not freq_s.isdigit():
                continue  # 含空格词条（如 "city walk"）自动跳过
            freq = int(freq_s)
            tag = parts[2] if len(parts) > 2 else None
            if word in seen:
                continue  # 去重
            seen.add(word)
            try:
                jieba.add_word(word, freq, tag)
                loaded += 1
            except Exception:
                pass  # 单个词条失败不影响整体加载
    return loaded


try:
    import jieba
    HAS_JIEBA = True

    # 加载自定义词典（如有）
    _load_custom_dict()
except ImportError:
    HAS_JIEBA = False
    jieba = None


# 简单的中文分词（不依赖 jieba）
# 基于常见的 2-gram 模式
def _fallback_tokenize(text: str) -> list:
    """无 jieba 时的简单分词

    策略：
    1. 先按标点分句
    2. 对每句用滑动窗口提取 1-4 字词
    3. 优先保留常见模式
    """
    import re
    if not text:
        return []

    # 1. 按标点分句
    sentences = re.split(r'''[，。！？、\s,.!?;:；：""''「」『』【】（）()\[\]]+''', text)
    tokens = []

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue

        # 2. 单字符切分 + 2字组合（粗粒度）
        chars = list(sent)
        for i, ch in enumerate(chars):
            # 单字
            if ch and not is_stopword(ch) and len(ch) >= 1:
                tokens.append(ch)
            # 2字组合
            if i + 1 < len(chars):
                two = ch + chars[i + 1]
                if two and not is_stopword(two):
                    tokens.append(two)
            # 3字组合（更细粒度，但减少噪音）
            if i + 2 < len(chars):
                three = ch + chars[i + 1] + chars[i + 2]
                if three and not is_stopword(three):
                    tokens.append(three)

    # 去重但保持顺序
    seen = set()
    result = []
    for t in tokens:
        if t not in seen:
            seen.add(t)
            result.append(t)
    return result


def tokenize(text: str, use_jieba: bool = True) -> list:
    """中文分词

    Args:
        text: 输入文本
        use_jieba: 是否使用 jieba（如果可用）

    Returns:
        词列表
    """
    if not text:
        return []

    if use_jieba and HAS_JIEBA:
        # v2.5.0：优先使用 jieba 精准分词。原实现用 pseg.cut（词性标注）
        # 但从未消费词性，词性标注比普通分词慢数倍；改回 jieba.cut。
        tokens = []
        for item in jieba.cut(text):
            word = str(item).strip()
            if word and not is_stopword(word):
                tokens.append(word)
        return tokens

    # Fallback: 简单中文分词（不依赖 jieba）
    return _fallback_tokenize(text)
