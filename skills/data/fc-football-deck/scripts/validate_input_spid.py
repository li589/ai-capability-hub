"""校验比赛 JSON 输入：每位非 ext 球员的 spid 必须在主库存在，且国籍必须与所属球队一致。
防止把别国球员的 spid 错填到本队，导致渲染出错位卡面。

合规后缀：home/away.name 可能带 "国家队套" "卡组" 等合规后缀，比对时自动剥离。
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 双引擎主库（根据 input 的 engine 字段选择）
_DB_PATHS = {
    'fco': ROOT / 'data/player_ptg_cache.json',
    'mobile': ROOT / 'data/mobile_player_cache.json',
}


def load_db(engine):
    path = _DB_PATHS.get(engine, _DB_PATHS['fco'])
    return json.load(open(path, encoding='utf-8'))

# 合规后缀剥离：把 "阿根廷国家队套" / "阿根廷卡组" / "阿根廷套" 都还原为 "阿根廷"
_SUFFIX_PATTERN = re.compile(r'(国家队套|国家队卡组|卡组|套|队)$')


# 中英国籍别名（双向）——数据补全后 nationality 可能是中文，run_match 传的可能是英文队名
_NATION_ALIAS = {
    "Congo DR": "刚果（金）", "刚果（金）": "Congo DR", "刚果金": "Congo DR",
    "刚果": "Congo DR", "DR Congo": "刚果（金）",
    "Cape Verde Islands": "佛得角", "佛得角": "Cape Verde Islands",
    "Korea Republic": "韩国", "South Korea": "韩国",
}


def normalize_nation(name):
    if not name:
        return name
    base = name.strip()
    # 反复剥离直到无后缀
    while True:
        new = _SUFFIX_PATTERN.sub('', base)
        if new == base:
            break
        base = new
    return base


def _name_mismatch(input_name, db_name):
    """名字是否明显对不上（防 spid 张冠李戴，如把德佩 spid 写成德容）。
    宽松匹配：任一方是另一方子串即视为一致（容忍'C罗'vs'C·罗纳尔多'这类）。"""
    if not input_name or not db_name:
        return False
    a = input_name.replace('·', '').replace('.', '').replace(' ', '').strip()
    b = db_name.replace('·', '').replace('.', '').replace(' ', '').strip()
    if not a or not b:
        return False
    return not (a in b or b in a)


def check(side_name, players, expected_nation, db, is_fallback=False):
    errors = []
    expected_base = normalize_nation(expected_nation)
    for p in players:
        spid = p.get('spid')
        # ext_ 占位、或无 spid（文字兜底队的核心球员，本就无真实卡）→ 跳过
        if isinstance(spid, str) and spid.startswith('ext_'):
            continue
        if not spid:
            # fallback 队允许无 spid 的文字球员；非 fallback 队则报错
            if is_fallback:
                continue
            errors.append(f"  ❌ {side_name} {p.get('name')} 缺少 spid（非兜底队必须有真实卡）")
            continue
        rec = db.get(str(spid))
        if not rec:
            errors.append(f"  ❌ {side_name} {p['name']} spid={spid} 不在主库")
            continue
        # 国籍核对：同时接受中文 nationality 与英文 nationality_en，并归一中英别名
        #（数据补全后刚果金等队 nationality 已中文化，但 run_match 可能传英文队名，两者都要认）
        actual = rec.get('nationality')
        actual_en = rec.get('nationality_en')
        candidates = {normalize_nation(actual), normalize_nation(actual_en),
                      _NATION_ALIAS.get(normalize_nation(actual), ''),
                      _NATION_ALIAS.get(normalize_nation(actual_en), '')}
        candidates.discard('')
        exp_set = {expected_base, _NATION_ALIAS.get(expected_base, '')}
        exp_set.discard('')
        if not (candidates & exp_set):
            errors.append(
                f"  ❌ {side_name} 期望 {p['name']}（{expected_nation} → {expected_base}），但 spid={spid} 实际是 {rec.get('name_cn')} ({actual})"
            )
        # 名字核对：防止 spid 张冠李戴（德佩 spid 写成德容会导致卡面错位）
        elif _name_mismatch(p.get('name', ''), rec.get('name_cn', '')):
            errors.append(
                f"  ❌ {side_name} spid={spid} 名字对不上：输入写「{p['name']}」，但该 spid 实际是「{rec.get('name_cn')}」(国籍 {actual} 正确，是 spid 填错了)"
            )
    return errors


def main(json_path):
    d = json.load(open(json_path, encoding='utf-8'))
    engine = d.get('engine', 'fco')
    db = load_db(engine)
    errors = []
    errors += check('home', d['home']['players'], d['home']['name'], db, d['home'].get('is_fallback', False))
    errors += check('away', d['away']['players'], d['away']['name'], db, d['away'].get('is_fallback', False))
    if errors:
        print(f'❌ 校验失败 {len(errors)} 处 (engine={engine}):')
        for e in errors:
            print(e)
        sys.exit(1)
    print(f'✓ 全部 spid 国籍校验通过 (engine={engine})')


if __name__ == '__main__':
    main(sys.argv[1])
