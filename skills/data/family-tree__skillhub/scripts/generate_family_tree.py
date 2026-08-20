import json
import re
import argparse
from typing import List, Optional, Dict, Any


def num_to_chinese(num):
    """将阿拉伯数字转换为对应的汉字数字"""
    chinese_numbers = ['一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
    try:
        num = int(num)
    except (ValueError, TypeError):
        return ""
    if num <= 10:
        return chinese_numbers[num - 1]
    elif num < 20:
        return f"十{chinese_numbers[num - 11] if num % 10 != 0 else ''}"
    elif num % 10 == 0:
        return f"{chinese_numbers[num // 10 - 1]}十"
    else:
        return f"{chinese_numbers[num // 10 - 1]}十{chinese_numbers[num % 10 - 1]}"

def age_sort_key(x):
    """按年龄排序（从大到小，空年龄排最后）"""
    age_str = str(x.get("age", "")).replace("岁", "").strip()
    try:
        return int(age_str) if age_str.isdigit() else 0
    except (ValueError, TypeError):
        return 0

def extract_number_prefix(text):
    """从文本中提取数字前缀（支持阿拉伯数字和汉字数字）"""
    # 先尝试提取阿拉伯数字
    match = re.search(r'(\d+)', text)
    if match:
        return match.group(1)
    
    # 再尝试提取汉字数字
    chinese_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, 
                    '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    for char, num in chinese_nums.items():
        if text.startswith(char):
            return str(num)
    
    return None

def generate_family_tree_html(family_members):

    lines_html = []
    cards_html = []

    """生成家庭关系图的HTML代码"""
    if not isinstance(family_members, list):
        family_members = []
    
    # 调整关系名称：将"自己"改为"客户自己"
    for member in family_members:
        if member.get("relation") == "自己":
            member["relation"] = "客户自己"
    
    # 确定客户性别（用于区分配偶父母关系）
    customer_gender = None
    customer_self = None
    for member in family_members:
        if member.get("relation") == "客户自己":
            customer_gender = member.get("gender")
            customer_self = member
            break
    
    # 分类家庭成员（按亲属关系分组）
    categories = {
        "父亲": None, "母亲": None, "配偶父母": [],
        "客户自己": customer_self, "妻子": None, "丈夫": None, 
        "配偶兄弟姐妹": [], "自己兄弟姐妹": [],
        "子女": [], "子女配偶": [], "孙辈": []
    }
    
    # 按关系分类成员
    for member in family_members:
        rel = member.get("relation", "").strip()
        if not rel:
            continue
        
        if rel == "客户自己":
            continue
        elif rel in ["父亲", "母亲"]:
            categories[rel] = member
        elif rel in ["岳父", "岳母", "公公", "婆婆"]:
            categories["配偶父母"].append(member)
        elif rel in ["妻子", "丈夫"]:
            categories[rel] = member
        elif rel in ["妻姐", "妻弟", "妻兄", "妻妹", "夫姐", "夫弟", "夫兄", "夫妹"]:
            categories["配偶兄弟姐妹"].append(member)
        elif rel in ["姐姐", "哥哥", "弟弟", "妹妹"]:
            categories["自己兄弟姐妹"].append(member)
        elif "儿子" in rel or "女儿" in rel:
            categories["子女"].append(member)
        elif "女婿" in rel or "儿媳" in rel:
            categories["子女配偶"].append(member)
        elif "孙子" in rel or "孙女" in rel or "外孙" in rel or "外孙女" in rel:
            categories["孙辈"].append(member)
    
    # 使用全局定义的年龄排序函数
    
    categories["配偶兄弟姐妹"].sort(key=age_sort_key, reverse=True)
    categories["自己兄弟姐妹"].sort(key=age_sort_key, reverse=True)
    categories["子女"].sort(key=age_sort_key, reverse=True)
    categories["孙辈"].sort(key=age_sort_key, reverse=True)
    
    # -------------------------- 自动补充自己父母 --------------------------
    # 当自己父母信息缺失时，自动补充
    if not categories["父亲"]:
        print("自动补充：父亲信息缺失，添加父亲卡片")
        categories["父亲"] = {
            "age": "未提及",
            "gender": "男",
            "job": "未提及",
            "marital_status": "已婚",
            "relation": "父亲",
            "parent": ""
        }
    
    if not categories["母亲"]:
        print("自动补充：母亲信息缺失，添加母亲卡片")
        categories["母亲"] = {
            "age": "未提及",
            "gender": "女",
            "job": "未提及",
            "marital_status": "已婚",
            "relation": "母亲",
            "parent": ""
        }
    
    # -------------------------- 自动补充配偶及配偶父母 --------------------------
    # 若客户自己有孩子但没有配偶和配偶父母的信息，则自动进行相应补充
    if categories["子女"] and not (categories["妻子"] or categories["丈夫"]):
        print("自动补充：有子女但无配偶信息，添加配偶卡片")
        
        # 根据客户性别确定配偶关系
        if customer_gender == "男":
            spouse_rel = "妻子"
            spouse_gender = "女"
        elif customer_gender == "女":
            spouse_rel = "丈夫"
            spouse_gender = "男"
        else:
            spouse_rel = "配偶"
            spouse_gender = "未提及"
        
        # 添加配偶信息
        categories[spouse_rel] = {
            "age": "未提及",
            "gender": spouse_gender,
            "job": "未提及",
            "marital_status": "已婚",
            "relation": spouse_rel,
            "parent": ""
        }
        
        # 添加配偶父母信息
        spouse_parents_added = False
        
        # 检查配偶父母是否已存在
        existing_spouse_parents = len(categories["配偶父母"]) > 0
        
        if not existing_spouse_parents:
            print("自动补充：配偶父母信息缺失，添加配偶父母卡片")
            
            # 根据客户性别确定配偶父母关系
            if customer_gender == "男":
                # 男性客户的配偶父母是岳父、岳母
                father_rel = "岳父"
                mother_rel = "岳母"
            elif customer_gender == "女":
                # 女性客户的配偶父母是公公、婆婆
                father_rel = "公公"
                mother_rel = "婆婆"
            else:
                # 性别信息缺失时使用通用称呼
                father_rel = "配偶父亲"
                mother_rel = "配偶母亲"
            
            # 添加配偶父亲
            categories["配偶父母"].append({
                "age": "未提及",
                "gender": "男",
                "job": "未提及",
                "marital_status": "已婚",
                "relation": father_rel,
                "parent": ""
            })
            
            # 添加配偶母亲
            categories["配偶父母"].append({
                "age": "未提及",
                "gender": "女",
                "job": "未提及",
                "marital_status": "已婚",
                "relation": mother_rel,
                "parent": ""
            })
    
    # -------------------------- 当配偶存在但配偶父母信息不完整时自动补充 --------------------------
    # 当配偶存在，但配偶父母信息不完整时，补充缺失的配偶父母信息
    if categories["妻子"] or categories["丈夫"]:
        # 检查是否已有配偶父亲和配偶母亲
        has_spouse_father = False
        has_spouse_mother = False
        
        for member in categories["配偶父母"]:
            rel = member.get("relation", "")
            if customer_gender == "男":
                if rel == "岳父":
                    has_spouse_father = True
                elif rel == "岳母":
                    has_spouse_mother = True
            elif customer_gender == "女":
                if rel == "公公":
                    has_spouse_father = True
                elif rel == "婆婆":
                    has_spouse_mother = True
            else:
                if rel == "配偶父亲":
                    has_spouse_father = True
                elif rel == "配偶母亲":
                    has_spouse_mother = True
        
        # 根据客户性别确定配偶父母关系称谓
        if customer_gender == "男":
            father_rel = "岳父"
            mother_rel = "岳母"
        elif customer_gender == "女":
            father_rel = "公公"
            mother_rel = "婆婆"
        else:
            father_rel = "配偶父亲"
            mother_rel = "配偶母亲"
        
        # 补充缺失的配偶父亲
        if not has_spouse_father:
            print(f"自动补充：配偶父亲信息缺失，添加{father_rel}卡片")
            categories["配偶父母"].append({
                "age": "未提及",
                "gender": "男",
                "job": "未提及",
                "marital_status": "已婚",
                "relation": father_rel,
                "parent": ""
            })
        
        # 补充缺失的配偶母亲
        if not has_spouse_mother:
            print(f"自动补充：配偶母亲信息缺失，添加{mother_rel}卡片")
            categories["配偶父母"].append({
                "age": "未提及",
                "gender": "女",
                "job": "未提及",
                "marital_status": "已婚",
                "relation": mother_rel,
                "parent": ""
            })
    
    # 根据性别和年龄重新确定子女关系（大儿子、二儿子...；大女儿、二女儿...）
    male_children = [child for child in categories["子女"] if child.get("gender") == "男"]
    female_children = [child for child in categories["子女"] if child.get("gender") == "女"]
    
    # 使用全局定义的数字转汉字函数

    for i, child in enumerate(male_children, 1):
        if i == 1:
            child["relation"] = "大儿子"
        elif i == len(male_children):
            child["relation"] = "小儿子"
        else:
            child["relation"] = f"{num_to_chinese(i)}儿子"  # 使用汉字数字前缀，如"二儿子"、"三儿子"

    # 对女儿进行排序并重新命名
    for i, child in enumerate(female_children, 1):
        if i == 1:
            child["relation"] = "大女儿"
        elif i == len(female_children):
            child["relation"] = "小女儿"
        else:
            child["relation"] = f"{num_to_chinese(i)}女儿"  # 使用汉字数字前缀，如"二女儿"、"三女儿"
        
        # 生成家庭成员卡片HTML
        cards_html = []
        lines_html = []  # 连接线HTML
    
    # -------------------------- 第一排：父母、配偶父母 --------------------------
    first_row_positions = {
        "父亲": {"left": 400, "top": 100},
        "母亲": {"left": 600, "top": 100},
        "配偶父亲": {"left": 800, "top": 100},
        "配偶母亲": {"left": 1000, "top": 100}
    }
    
    # 处理父亲、母亲卡片
    for rel in ["父亲", "母亲"]:
        member = categories[rel]
        if member:
            pos = first_row_positions[rel]
            # 身故成员用特殊样式：job为"身故"表示身故
            card_class = "deceased" if member.get("job") == "身故" else "other-members"
            cards_html.append(f'''
            <div class="person-card {card_class}" style="left: {pos['left']}px; top: {pos['top']}px;">
                <span>{rel}</span>
                <div>
                    <span>{member.get('age', '')}</span>
                    <i></i>
                    <span>{member.get('job', '')}</span>
                </div>
            </div>''')
    
    # 处理配偶父母（岳父/岳母 或 公公/婆婆）
    spouse_father = None
    spouse_mother = None
    for member in categories["配偶父母"]:
        if customer_gender == "男":
            # 男性客户的配偶父母是岳父、岳母
            if member.get("relation") == "岳父":
                spouse_father = member
            elif member.get("relation") == "岳母":
                spouse_mother = member
        elif customer_gender == "女":
            # 女性客户的配偶父母是公公、婆婆
            if member.get("relation") == "公公":
                spouse_father = member
            elif member.get("relation") == "婆婆":
                spouse_mother = member
    
    # 配偶父亲卡片
    if spouse_father:
        pos = first_row_positions["配偶父亲"]
        card_class = "deceased" if spouse_father.get("job") == "身故" else "other-members"
        cards_html.append(f'''
        <div class="person-card {card_class}" style="left: {pos['left']}px; top: {pos['top']}px;">
            <span>{spouse_father.get('relation', '')}</span>
            <div>
                <span>{spouse_father.get('age', '')}</span>
                <i></i>
                <span>{spouse_father.get('job', '')}</span>
            </div>
        </div>''')
    
    # 配偶母亲卡片
    if spouse_mother:
        pos = first_row_positions["配偶母亲"]
        card_class = "deceased" if spouse_mother.get("job") == "身故" else "other-members"
        cards_html.append(f'''
        <div class="person-card {card_class}" style="left: {pos['left']}px; top: {pos['top']}px;">
            <span>{spouse_mother.get('relation', '')}</span>
            <div>
                <span>{spouse_mother.get('age', '')}</span>
                <i></i>
                <span>{spouse_mother.get('job', '')}</span>
            </div>
        </div>''')
    
    # -------------------------- 第二排：客户自己、配偶、兄弟姐妹 --------------------------
    # 客户自己卡片
    if categories["客户自己"]:
        self_member = categories["客户自己"]
        self_class = "deceased" if self_member.get("job") == "身故" else "self-and-spouse"
        cards_html.append(f'''
        <div class="person-card {self_class}" style="left: 500px; top: 200px;">
            <span>客户</span>
            <div>
                <span>{self_member.get('age', '')}</span>
                <i></i>
                <span>{self_member.get('job', '')}</span>
            </div>
        </div>''')
    
    # 配偶卡片（妻子/丈夫）
    spouse_rel = "妻子" if categories["妻子"] else "丈夫" if categories["丈夫"] else None
    if spouse_rel and categories[spouse_rel]:
        spouse = categories[spouse_rel]
        spouse_class = "deceased" if spouse.get("job") == "身故" else "self-and-spouse"
        cards_html.append(f'''
        <div class="person-card {spouse_class}" style="left: 900px; top: 200px;">
            <span>{spouse_rel}</span>
            <div>
                <span>{spouse.get('age', '')}</span>
                <i></i>
                <span>{spouse.get('job', '')}</span>
            </div>
        </div>''')
    
    # 自己的兄弟姐妹（客户左侧排列）
    current_left = 500 - 110  # 从客户左侧40px开始
    for sibling in categories["自己兄弟姐妹"]:
        rel = sibling.get("relation", "")
        card_class = "deceased" if sibling.get("job") == "身故" else "light-green-member"
        cards_html.append(f'''
        <div class="person-card {card_class}" style="left: {current_left}px; top: 205px;">
            <span>{rel}</span>
            <div>
                <span>{sibling.get('age', '')}</span>
                <i></i>
                <span>{sibling.get('job', '')}</span>
            </div>
        </div>''')
        current_left -= 110  # 每个兄弟姐妹向左偏移40px
    
    # 配偶的兄弟姐妹（配偶右侧排列）
    current_left = 900 + 110  # 从配偶右侧40px开始
    for sibling in categories["配偶兄弟姐妹"]:
        rel = sibling.get("relation", "")
        card_class = "deceased" if sibling.get("job") == "身故" else "light-green-member"
        cards_html.append(f'''
        <div class="person-card {card_class}" style="left: {current_left}px; top: 205px;">
            <span>{rel}</span>
            <div>
                <span>{sibling.get('age', '')}</span>
                <i></i>
                <span>{sibling.get('job', '')}</span>
            </div>
        </div>''')
        current_left += 110  # 每个兄弟姐妹向右偏移40px
    
    # -------------------------- 第三排：子女 --------------------------
    child_positions = {}  # 记录子女的位置，用于后续配偶/孙辈定位
    if categories["子女"]:
        # 使用全局定义的年龄排序函数

        # 找到年龄最大的子女
        oldest_child = max(categories["子女"], key=age_sort_key)

        # 按性别分组，并排除年龄最大的子女
        male_children = [c for c in categories["子女"] if c.get("gender") == "男" and c != oldest_child]
        female_children = [c for c in categories["子女"] if c.get("gender") == "女" and c != oldest_child]

        # 按年龄从大到小排序
        male_children.sort(key=age_sort_key, reverse=True)
        female_children.sort(key=age_sort_key, reverse=True)

        # 放置年龄最大的子女在中间
        rel = oldest_child.get("relation", "")
        card_class = "deceased" if oldest_child.get("job") == "身故" else "other-members"
        cards_html.append(f'''
        <div class="person-card {card_class}" style="left: 700px; top: 310px;">
            <span>{rel}</span>
            <div>
                <span>{oldest_child.get('age', '')}</span>
                <i></i>
                <span>{oldest_child.get('job', '')}</span>
            </div>
        </div>''')
        child_positions[rel] = 700

        # 放置剩下的男性子女在中间左边，年龄越大离中间越近
        for i, child in enumerate(male_children, start=1):
            rel = child.get("relation", "")
            card_class = "deceased" if child.get("job") == "身故" else "other-members"
            current_left = 700 - i * 140
            cards_html.append(f'''
            <div class="person-card {card_class}" style="left: {current_left}px; top: 310px;">
                <span>{rel}</span>
                <div>
                    <span>{child.get('age', '')}</span>
                    <i></i>
                    <span>{child.get('job', '')}</span>
                </div>
            </div>''')
            child_positions[rel] = current_left

        # 放置剩下的女性子女在中间右边，年龄越大离中间越近
        for i, child in enumerate(female_children, start=1):
            rel = child.get("relation", "")
            card_class = "deceased" if child.get("job") == "身故" else "other-members"
            current_left = 700 + i * 140
            cards_html.append(f'''
            <div class="person-card {card_class}" style="left: {current_left}px; top: 310px;">
                <span>{rel}</span>
                <div>
                    <span>{child.get('age', '')}</span>
                    <i></i>
                    <span>{child.get('job', '')}</span>
                </div>
            </div>''')
            child_positions[rel] = current_left
    
    # -------------------------- 检查并自动添加子女配偶 --------------------------
    # 遍历所有孙辈，找出有孙辈但没有配偶的子女
    if categories["孙辈"]:
        # 创建一个集合保存已经有配偶的子女关系
        children_with_spouse = set()
        existing_spouse_relations = set()
        
        # 找出已经有配偶的子女并记录所有已存在的配偶关系
        for spouse in categories["子女配偶"]:
            spouse_rel = spouse.get("relation", "")
            existing_spouse_relations.add(spouse_rel)
            
            # 提取配偶对应的子女关系
            if "儿媳" in spouse_rel:
                # 儿媳对应的是儿子
                child_rel = spouse_rel.replace("儿媳", "儿子")
                children_with_spouse.add(child_rel)
            elif "女婿" in spouse_rel:
                # 女婿对应的是女儿
                child_rel = spouse_rel.replace("女婿", "女儿")
                children_with_spouse.add(child_rel)
        
        # 遍历所有有孙辈的子女，检查是否需要添加配偶
        # 先收集所有有孙辈的父母，避免重复处理
        parents_with_grandchildren = set()
        for grandchild in categories["孙辈"]:
            parent = grandchild.get("parent", "").strip()
            if parent:
                parents_with_grandchildren.add(parent)
                print(f"发现孙辈，父节点: {parent}")
        
        # 处理每个有孙辈但没有配偶的父母
        for parent in parents_with_grandchildren:
            print(f"检查父节点: {parent}，是否已有配偶: {parent in children_with_spouse}")
            if parent not in children_with_spouse:
                # 查找对应的子女
                target_child = next((c for c in categories["子女"] if c.get("relation") == parent), None)
                if target_child:
                    # 创建新的配偶对象
                    spouse = {
                        "age": "未提及",
                        "job": "未提及",
                        "marital_status": "已婚",
                        "parent": ""
                    }
                    
                    # 根据子女关系设置配偶关系
                    if "儿子" in parent:
                        spouse["relation"] = parent.replace("儿子", "儿媳")
                        spouse["gender"] = "女"
                    elif "女儿" in parent:
                        spouse["relation"] = parent.replace("女儿", "女婿")
                        spouse["gender"] = "男"
                    
                    # 添加到子女配偶列表（确保不会重复添加）
                    if spouse.get("relation") and spouse["relation"] not in existing_spouse_relations:
                        print(f"添加配偶: {spouse['relation']} 对应 {parent}")
                        categories["子女配偶"].append(spouse)
                        children_with_spouse.add(parent)
                        existing_spouse_relations.add(spouse["relation"])
    
    # -------------------------- 第四排：子女配偶（儿媳/女婿） --------------------------
    if categories["子女配偶"]:
        # 为子女配偶创建映射关系
        spouse_to_child_mapping = []
        
        # 为每个子女配偶确定对应的子女
        for spouse in categories["子女配偶"]:
            rel = spouse.get("relation", "")
            target_child = None
            
            # 根据配偶关系查找对应的子女
            if "儿媳" in rel:
                # 查找儿子
                if "大儿媳" == rel:
                    target_child = next((c for c in categories["子女"] if c.get("relation") == "大儿子"), None)
                elif "二儿媳" == rel:
                    target_child = next((c for c in categories["子女"] if c.get("relation") == "二儿子"), None)
                elif "小儿媳" == rel:
                    target_child = next((c for c in categories["子女"] if c.get("relation") == "小儿子"), None)
                else:
                    # 尝试提取数字前缀
                    num = extract_number_prefix(rel)
                    if num:
                        target_child = next((c for c in categories["子女"] if c.get("relation") == f"{num_to_chinese(num)}儿子"), None)
            elif "女婿" in rel:
                # 查找女儿
                if "大女婿" == rel:
                    target_child = next((c for c in categories["子女"] if c.get("relation") == "大女儿"), None)
                elif "二女婿" == rel:
                    target_child = next((c for c in categories["子女"] if c.get("relation") == "二女儿"), None)
                elif "小女婿" == rel:
                    target_child = next((c for c in categories["子女"] if c.get("relation") == "小女儿"), None)
                else:
                    # 尝试提取数字前缀
                    num = extract_number_prefix(rel)
                    if num:
                        target_child = next((c for c in categories["子女"] if c.get("relation") == f"{num_to_chinese(num)}女儿"), None)
            
            # 保存配偶与子女的映射关系
            if target_child:
                spouse_to_child_mapping.append((spouse, target_child))
        
        # 为每个子女配偶生成HTML卡片
        for spouse, target_child in spouse_to_child_mapping:
            if target_child.get("relation") in child_positions:
                child_left = child_positions[target_child.get("relation")]
                rel = spouse.get("relation", "")
                card_class = "deceased" if spouse.get("job") == "身故" else "light-green-member"
                cards_html.append(f'''
                <div class="person-card {card_class}" style="left: {child_left}px; top: 370px;">
                    <span>{rel}</span>
                    <div>
                        <span>{spouse.get('age', '')}</span>
                        <i></i>
                        <span>{spouse.get('job', '')}</span>
                    </div>
                </div>''')
    
    # -------------------------- 第五排：孙辈 --------------------------
    if categories["孙辈"]:
        # 按父节点分组孙辈
        grandchildren_by_parent = {}
        for grandchild in categories["孙辈"]:
            parent = grandchild.get("parent", "").strip()
            if parent:
                if parent not in grandchildren_by_parent:
                    grandchildren_by_parent[parent] = []
                grandchildren_by_parent[parent].append(grandchild)
        
        # 对每个父节点的孙辈进行年龄排序并生成卡片
        for parent, grandchildren in grandchildren_by_parent.items():
            # 查找父节点对应的子女
            target_child = next((c for c in categories["子女"] if c.get("relation") == parent), None)
            
            if target_child and target_child.get("relation") in child_positions:
                child_left = child_positions[target_child.get("relation")]
                
                # 按年龄从大到小排序孙辈
                grandchildren.sort(key=lambda x: int(str(x.get("age", "0").replace("岁", "").strip())), reverse=True)
                
                # 计算每个孙辈的垂直位置，间隔10px
                base_top = 430  # 基础垂直位置
                for i, grandchild in enumerate(grandchildren):
                    rel = grandchild.get("relation", "")
                    card_class = "deceased" if grandchild.get("job") == "身故" else "other-members"
                    current_top = base_top + i * 60  # 每个孙辈卡片高度50px + 间隔10px
                    cards_html.append(f'''
                    <div class="person-card {card_class}" style="left: {child_left}px; top: {current_top}px;">
                        <span>{rel}</span>
                        <div>
                            <span>{grandchild.get('age', '')}</span>
                            <i></i>
                            <span>{grandchild.get('job', '')}</span>
                        </div>
                    </div>''')
    
    # -------------------------- 生成连接线 --------------------------
    # 1. 父母之间的连接（实线/离婚虚线）
    if categories["父亲"] and categories["母亲"]:
        line_class = "dashed-line" if categories["父亲"].get("marital_status") == "离婚" else "connection-line"
        lines_html.append(f'''
        <div class="{line_class}" style="left: 500px; top: 125px; width: 100px; height: 0.5px;"></div>''')
    
    # 2. 配偶父母之间的连接
    if spouse_father and spouse_mother:
        line_class = "dashed-line" if spouse_father.get("marital_status") == "离婚" else "connection-line"
        lines_html.append(f'''
        <div class="{line_class}" style="left: 900px; top: 125px; width: 100px; height: 0.5px;"></div>''')
    
    # 3. 客户与配偶之间的连接
    if categories["客户自己"] and (categories["妻子"] or categories["丈夫"]):
        line_class = "dashed-line" if categories["客户自己"].get("marital_status") == "离婚" else "connection-line"
        lines_html.append(f'''
        <div class="{line_class}" style="left: 600px; top: 230px; width: 300px; height: 0.5px;"></div>''')
    
    # 4. 父母与客户之间的垂直连接
    if (categories["父亲"] or categories["母亲"]) and categories["客户自己"]:
        lines_html.append(f'''
        <div class="connection-line" style="left: 550px; top: 125px; width: 0.5px; height: 75px;"></div>''')
    
    # 5. 配偶父母与配偶之间的垂直连接
    if (spouse_father or spouse_mother) and (categories["妻子"] or categories["丈夫"]):
        lines_html.append(f'''
        <div class="connection-line" style="left: 950px; top: 125px; width: 0.5px; height: 75px;"></div>''')
    
    # 6. 客户与年龄最大子女的垂直连接
    if categories["子女"] and categories["客户自己"]:
        lines_html.append(f'''
        <div class="connection-line" style="left: 750px; top: 230px; width: 0.5px; height: 80px;"></div>''')
      
    # 7. 子女之间的连接
    if len(categories["子女"]) > 1:
        # 获取所有子女的位置并按从左到右排序
        child_rels = [child.get("relation") for child in categories["子女"]]
        child_lefts = [child_positions[rel] for rel in child_rels if rel in child_positions]
        child_lefts.sort()  # 按水平位置从左到右排序
        
        # 生成连接线：数量为子女数-1
        for i in range(len(child_lefts) - 1):
            # 左边子女位置+100px作为连接线起点
            line_left = child_lefts[i] + 100
            lines_html.append(f'''
            <div class="connection-line" style="left: {line_left}px; top: 335px; width: 40px; height: 0.5px;"></div>''')

    # 计算family-tree容器的动态大小
    # 1. 收集所有卡片的位置信息
    min_left = float('inf')
    max_right = 0
    min_top = float('inf')
    max_bottom = 0
    
    # 卡片宽度和高度（根据CSS中的定义）
    card_width = 100
    card_height = 50
    
    # 从cards_html中提取位置信息
    for card_html in cards_html:
        left_match = re.search(r'left: (\d+)px', card_html)
        top_match = re.search(r'top: (\d+)px', card_html)
        
        if left_match and top_match:
            left = int(left_match.group(1))
            top = int(top_match.group(1))
            
            # 计算卡片的边界
            right = left + card_width
            bottom = top + card_height
            
            # 更新极值
            min_left = min(min_left, left)
            max_right = max(max_right, right)
            min_top = min(min_top, top)
            max_bottom = max(max_bottom, bottom)
    
    # 2. 确保有卡片数据，如果没有则使用默认值
    if min_left == float('inf'):
        container_width = 1500
        container_height = 600
        container_left = 0
        container_top = 0
    else:
        # 3. 计算容器大小（添加100px边距）
        container_width = max_right - min_left + 200  # 左右各100px边距
        container_height = max_bottom - min_top + 200  # 上下各100px边距
        
        # 确保容器大小至少为默认值
        container_width = max(container_width, 1500)
        container_height = max(container_height, 600)
    
    # 生成完整HTML
    html = f'''
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>客户家族关系图</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
            margin: 0;
            background-color: #f0f0f0;
            overflow: auto;
        }}
        .family-tree {{
            position: relative;
            width: {container_width}px;
            height: {container_height}px;
            background-color: #fff;
            border: 1px solid #ccc;
        }}
        .person-card {{
            border-radius: 4px;
            text-align: center;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            position: absolute;
        }}
        .person-card span {{
            width: 70px;
            border-bottom: 0.5px solid white;
            padding-bottom: 5px;
            margin-bottom: 5px;
            font-size: 10px;
        }}
        .person-card div {{
            display: flex;
            align-items: center;
            font-size: 8px;
        }}
        .person-card div span {{
            width: auto;
            border-bottom: none;
            padding: 0 5px;
            margin: 0;
        }}
        .person-card div i {{
            width: 0.5px;
            height: 15px;
            background-color: white;
        }}
        .self-and-spouse {{
            width: 100px;
            height: 60px;
            background-color: red;
            border: 0.5px solid #d3d3d3;
            color: white;
            font-weight: bold;
        }}       
        .grandchildren {{
            width: 100px;
            height: 25px;
            border-radius: 5px;
            background-color: green;
            border: 0.5px solid #d3d3d3;
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .other-members {{
            width: 100px;
            height: 50px;
            background-color: green;
            border: 0.5px solid #d3d3d3;
            color: white;
        }}
        .light-green-member {{
            width: 100px;
            height: 50px;
            background-color: #90EE90;
            border: 0.5px solid #d3d3d3;
            color: black;
        }}
        .light-green-member span {{
            border-bottom: 0.5px solid black;
        }}
        .light-green-member div i {{
            background-color: black;
        }}
        .deceased {{
            width: 100px;
            height: 50px;
            background-color: lightgray;
            border: 0.5px dashed #d3d3d3;
            color: black;
        }}
        .connection-line {{
            position: absolute;
            background-color: black;
        }}
        .dashed-line {{
            position: absolute;
            border: 1px dashed black;
            background-color: transparent;
        }}
    </style>
</head>
<body>
    <div class="family-tree">
        {''.join(cards_html)}
        {''.join(lines_html)}
    </div>
</body>
</html>
    '''
    return html.strip()


def main():
    parser = argparse.ArgumentParser(description='生成家庭结构图HTML')
    parser.add_argument('--input_json', required=True, help='输入JSON文件路径')
    parser.add_argument('--output_html', required=True, help='输出HTML文件路径')
    
    args = parser.parse_args()
    
    # 读取输入JSON
    with open(args.input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    family_members = data.get('family_members', [])
    
    # 生成HTML
    html_content = generate_family_tree_html(family_members)
    
    # 写入输出文件
    with open(args.output_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"成功生成家庭结构图HTML: {args.output_html}")
    print(f"共处理 {len(family_members)} 个家庭成员")


if __name__ == '__main__':
    main()

