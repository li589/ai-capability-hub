"""
数据修正脚本
修正持仓数据库中的类型字段
"""
import json
import os

# 使用相对于脚本位置的路径，增强跨平台兼容性
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_DIR = os.path.join(BASE_DIR, 'data')

def fix_holdings_database():
    """修正持仓数据库中的类型字段"""
    filepath = os.path.join(DATA_DIR, 'holdings_database.json')

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    holdings = data.get('holdings', [])

    # 统计修正前的类型
    types_before = {}
    for h in holdings:
        t = h.get('type', 'unknown')
        types_before[t] = types_before.get(t, 0) + 1

    print(f"修正前类型分布: {types_before}")

    # 修正：如果没有type字段，根据其他字段判断
    for h in holdings:
        if h.get('type') == 'unknown' or 'type' not in h:
            if 'stock_code' in h or 'stock_name' in h:
                h['type'] = 'stock'
            elif 'bond_code' in h or 'bond_name' in h:
                h['type'] = 'bond'

    # 统计修正后的类型
    types_after = {}
    for h in holdings:
        t = h.get('type', 'unknown')
        types_after[t] = types_after.get(t, 0) + 1

    print(f"修正后类型分布: {types_after}")

    # 保存
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已保存修正后的数据")

def add_investment_style():
    """为经理数据添加投资风格信息"""
    filepath = os.path.join(DATA_DIR, 'fund_managers.json')

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    managers = data.get('managers', [])

    # 为有持仓的经理添加投资风格描述
    for m in managers:
        if m.get('top_stocks') and not m.get('investment_style'):
            # 根据持仓判断风格
            stocks = m.get('top_stocks', [])
            if stocks:
                # 简单规则：如果重仓股有科技类，标记为成长型
                tech_keywords = ['科技', '新能源', '半导体', '芯片', '人工智能', '软件']
                has_tech = any(any(kw in s.get('stock_name', '') for kw in tech_keywords) for s in stocks)

                if has_tech:
                    m['investment_style'] = '成长型'
                else:
                    m['investment_style'] = '均衡型'

    # 保存
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已更新 {len(managers)} 个经理的投资风格")

def main():
    print("=" * 50)
    print("数据修正")
    print("=" * 50)

    fix_holdings_database()
    add_investment_style()

    print("\\n修正完成!")

if __name__ == "__main__":
    main()