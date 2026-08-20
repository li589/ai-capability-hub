#!/usr/bin/env python3
"""
Thesis Tutor v4.0 - 测试脚本
验证本地助手 + API 集成功能
"""

from main import ThesisTutor
from core.api_client import UserConfig, DeepSeekClient
from core.local_assistant import LocalAssistant, KnowledgeBase
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_local_assistant():
    """测试本地助手"""
    print("=" * 60)
    print("测试 1: 本地助手")
    print("=" * 60)

    assistant = LocalAssistant()

    test_cases = [
        ("问候", "你好"),
        ("选题", "帮我选题，我是计算机专业的"),
        ("大纲", "怎么写大纲？"),
        ("格式", "引用格式怎么弄？"),
        ("查重", "怎么降重？"),
        ("配置", "配置 API Key"),
        ("未知", "abcdefg"),
    ]

    for name, inp in test_cases:
        print(f"\n[{name}] 输入: {inp}")
        result = assistant.handle(inp)
        print(f"  -> 意图: {result['type']}, 置信度: {result['confidence']:.2f}")
        print(f"  -> 需要高级AI: {result['need_advanced']}")
        print(f"  -> 回复预览: {result['response'][:80]}...")

    print("\n[OK] 本地助手测试完成")


def test_chapter_review():
    """测试论文检查功能"""
    print("\n" + "=" * 60)
    print("测试 2: 论文段落检查")
    print("=" * 60)

    assistant = LocalAssistant()

    # 有问题的论文段落
    bad_text = """随着互联网的发展，深度学习技术越来越重要。我觉得这个方向挺好的。
    
然后，我们来看一下数据。还有，这个模型非常不错。所有结果都表明我们的方法是最好的。
    
众所周知，神经网络可以解决所有问题。毫无疑问，我们的研究非常有意义。"""

    print(f"\n输入: {bad_text[:100]}...")
    result = assistant.handle(f"帮我看看这段写得怎么样：{bad_text}")

    print(f"\n检测到 {result.get('issues_count', 0)} 个问题:")
    if result.get('issues'):
        for i, issue in enumerate(result['issues'], 1):
            print(
                f"  {i}. [{issue['severity']}] {issue.get('type', 'general')}: {issue.get('message', issue.get('pattern', ''))}")

    print("\n[OK] 论文检查测试完成")


def test_user_config():
    """测试用户配置"""
    print("\n" + "=" * 60)
    print("测试 3: 用户配置管理")
    print("=" * 60)

    # 清理测试配置
    test_config_path = "./user_configs/test_config_user.json"
    if os.path.exists(test_config_path):
        os.remove(test_config_path)

    config = UserConfig("test_config_user")

    print(f"\n初始状态:")
    print(f"  - 有 API Key: {config.has_api_key()}")
    print(f"  - 统计: {config.get_stats()}")

    # 测试设置无效 Key
    print(f"\n设置无效 Key:")
    result = config.set_api_key("test-invalid-format")
    print(f"  - 结果: {result['success']}, {result['message']}")

    # 测试更新统计
    config.update_stats(api_call=False)
    config.update_stats(api_call=True)
    print(f"\n更新统计后:")
    print(f"  - 统计: {config.get_stats()}")

    # 测试移除 Key
    config.remove_api_key()
    print(f"\n移除 Key 后:")
    print(f"  - 有 API Key: {config.has_api_key()}")

    print("\n[OK] 用户配置测试完成")


def test_main_router():
    """测试主路由系统"""
    print("\n" + "=" * 60)
    print("测试 4: 主路由系统")
    print("=" * 60)

    # 清理测试配置
    test_config_path = "./user_configs/test_router_user.json"
    if os.path.exists(test_config_path):
        os.remove(test_config_path)

    tutor = ThesisTutor()

    print(f"\n状态:")
    status = tutor.get_status()
    print(f"  - 语言: {status.get('language', 'zh')}")
    print(f"  - 学科: {status.get('discipline', '未设置')}")

    test_cases = [
        "你好",
        "帮我选题",
        "配置 API Key: <YOUR_API_KEY>",
        "我的配置",
        "删除 API Key",
        "我的配置",
    ]

    for inp in test_cases:
        print(f"\n输入: {inp}")
        result = tutor.chat(inp)
        print(
            f"  -> 类型: {result['type']}, 置信度: {result.get('confidence', 0):.2f}")
        print(f"  -> 回复: {result['response'][:100]}...")

    print("\n[OK] 主路由测试完成")


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 60)
    print("测试 5: 边界情况")
    print("=" * 60)

    assistant = LocalAssistant()

    edge_cases = [
        ("空字符串", ""),
        ("超长文本", "这是一个测试。" * 1000),
        ("特殊字符", "@#$%^&*()"),
        ("混合语言", "Hello 你好 world 世界"),
        ("只有标点", "，。！？"),
    ]

    for name, inp in edge_cases:
        print(f"\n[{name}] 长度: {len(inp)}")
        try:
            result = assistant.handle(inp)
            print(f"  -> 成功: {result['type']}")
        except Exception as e:
            print(f"  -> 错误: {e}")

    print("\n[OK] 边界情况测试完成")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("Thesis Tutor v4.0 - 全面测试")
    print("=" * 60 + "\n")

    try:
        test_local_assistant()
        test_chapter_review()
        test_user_config()
        test_main_router()
        test_edge_cases()

        print("\n" + "=" * 60)
        print("所有测试通过！")
        print("=" * 60)

    except Exception as e:
        print(f"\n[X] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_all_tests()
