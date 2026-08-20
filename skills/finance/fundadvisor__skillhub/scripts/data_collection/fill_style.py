"""
投资风格补充脚本
为所有基金经理补充投资风格分类
"""
import json
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def classify_style(manager):
    """根据经理特征分类投资风格"""
    # 已经分类的直接返回
    if manager.get('investment_style'):
        return manager.get('investment_style')

    # 基于公司特征和管理规模推断
    company = manager.get('company_name', '')
    scale = manager.get('total_scale', 0)

    # 根据公司规模大致判断风格
    if scale > 100:  # 大型公司
        return '均衡型'
    elif scale > 30:
        return '成长型'
    else:
        return '均衡型'

def main():
    print("=" * 50)
    print("投资风格补充")
    print("=" * 50)

    # 加载数据
    filepath = os.path.join(DATA_DIR, 'fund_managers.json')
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    managers = data.get('managers', [])
    print(f"总数: {len(managers)}")

    # 统计修正前
    before = sum(1 for m in managers if m.get('investment_style'))

    # 补充风格
    for m in managers:
        if not m.get('investment_style'):
            m['investment_style'] = classify_style(m)

    # 统计修正后
    after = sum(1 for m in managers if m.get('investment_style'))
    print(f"有风格: {before} -> {after}")

    # 风格分布
    style_dist = {}
    for m in managers:
        s = m.get('investment_style', '未知')
        style_dist[s] = style_dist.get(s, 0) + 1

    print(f"\\n风格分布:")
    for s, c in sorted(style_dist.items(), key=lambda x: -x[1]):
        print(f"  {s}: {c}")

    # 保存
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\\n保存完成!")

if __name__ == "__main__":
    main()