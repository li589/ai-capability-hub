#!/usr/bin/env python3
"""梅花易数专业起卦解卦 — 独立CLI版

邵雍正宗先天数算法，零依赖，直接运行。

用法:
    python3 meihua.py --query "升职" --tier detailed
    python3 meihua.py --query "感情" --method number --numbers 3 7
    python3 meihua.py --query "运势" --method char --text "顺其自然"
"""

import argparse
import datetime
import json
import sys
from typing import Optional, Tuple


# ============================================================
# 八卦基础数据
# ============================================================

XIANTIAN_NUM = {1:'乾',2:'兑',3:'离',4:'震',5:'巽',6:'坎',7:'艮',8:'坤'}
TRIGRAM_ATTR = {
    '乾': {'nature':'天','element':'金','image':'刚健中正','body':'头首','direction':'西北','family':'父'},
    '兑': {'nature':'泽','element':'金','image':'喜悦和乐','body':'口舌','direction':'西','family':'少女'},
    '离': {'nature':'火','element':'火','image':'光明附丽','body':'目','direction':'南','family':'中女'},
    '震': {'nature':'雷','element':'木','image':'动而起','body':'足','direction':'东','family':'长男'},
    '巽': {'nature':'风','element':'木','image':'柔顺入','body':'股','direction':'东南','family':'长女'},
    '坎': {'nature':'水','element':'水','image':'险而陷','body':'耳','direction':'北','family':'中男'},
    '艮': {'nature':'山','element':'土','image':'止而稳','body':'手','direction':'东北','family':'少男'},
    '坤': {'nature':'地','element':'土','image':'柔顺承载','body':'腹','direction':'西南','family':'母'},
}
TRIGRAM_BITS = {
    '乾':[1,1,1],'兑':[1,1,0],'离':[1,0,1],'震':[1,0,0],
    '巽':[0,1,1],'坎':[0,1,0],'艮':[0,0,1],'坤':[0,0,0],
}
BITS_TO_TRIGRAM = {tuple(v):k for k,v in TRIGRAM_BITS.items()}

WUXING_SHENG = {'木':'火','火':'土','土':'金','金':'水','水':'木'}
WUXING_KE = {'木':'土','土':'水','水':'火','火':'金','金':'木'}
MONTH_WANGLING = {1:'木',2:'木',3:'土',4:'火',5:'火',6:'土',7:'金',8:'金',9:'土',10:'水',11:'水',12:'土'}
DIZHI = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']

# ============================================================
# 64卦数据
# ============================================================

HEX = {
    ('乾','乾'):('乾为天','元亨利贞','天行健，君子以自强不息',
        '事业运势极佳，可大胆开拓，但过刚则折','感情强势需包容，桃花旺','注意头骨，阳气过盛宜清淡','财运亨通，适可而止'),
    ('乾','兑'):('天泽履','履虎尾不咥人亨','以柔行刚，谨慎恭敬则无险',
        '宜谦逊低调循规蹈矩','以诚相待，小心行事','注意口舌，饮食节制','财运平稳，稳健为上'),
    ('乾','离'):('天火同人','同人于野亨','志同道合，团结协作',
        '团队合作顺利，贵人旺','感情和谐，宜多社交','注意眼睛心脏','合作生财'),
    ('乾','震'):('天雷无妄','元亨利贞','顺应天道，真诚不妄为',
        '保持真诚，正道而行','以真心换真心','身心调养以自然为本','正财佳偏财弱'),
    ('乾','巽'):('天风姤','女壮勿用取女','一阴初生，防微杜渐',
        '注意小人暗算','感情有诱惑需定力','注意呼吸系统风寒','财运有暗耗防骗'),
    ('乾','坎'):('天水讼','有孚窒惕中吉终凶','天水相违，争讼之象',
        '易有争端宜协商','易有争吵需沟通','注意精神压力焦虑','财运不佳防纠纷'),
    ('乾','艮'):('天山遁','亨小利贞','阳退阴进，智者知退',
        '宜低调退让等待时机','给彼此空间','宜静养休息','财运偏弱宜守'),
    ('乾','坤'):('天地否','否之匪人不利君子贞','天地不交，闭塞不通',
        '沟通不畅上下隔阂','冷淡疏远需打破僵局','气机不畅宜开阔心胸','财运低迷宜减少开支'),
    ('兑','乾'):('泽天夬','扬于王庭','决断之象，果断除弊',
        '需果断决策不可拖延','明确态度不可暧昧','注意口腔牙齿','果断止损或加仓'),
    ('兑','兑'):('兑为泽','亨利贞','喜悦和乐，上下皆悦',
        '人际极佳口才出众','甜蜜快乐心意相通','心情愉悦注意口舌','人脉关系带来收益'),
    ('兑','离'):('泽火革','己日乃孚元亨利贞','变革更新，推陈出新',
        '面临变革顺应变化','改变相处模式','适合改变生活方式','理财方式需调整'),
    ('兑','震'):('泽雷随','元亨利贞无咎','随顺而动，顺势而为',
        '宜配合他人团队协作','顺应对方的节奏','顺应身体信号','跟随市场趋势'),
    ('兑','巽'):('泽风大过','栋桡利有攸往','承受过重，压力过大',
        '压力大需合理分配','付出过多需爱自己','身体负荷过重注意休息','负债偏高需减支'),
    ('兑','坎'):('泽水困','亨贞大人吉','困顿之象，守正可通',
        '遇到瓶颈坚持信念','陷入困境需耐心','亚健康需全面调理','财运低迷节俭度日'),
    ('兑','艮'):('泽山咸','亨利贞取女吉','感应之象，阴阳交感',
        '贵人感应合作自来','桃花旺盛缘分已到','注意关节四肢','合作投资有利'),
    ('兑','坤'):('泽地萃','亨王假有庙','聚集之象，人才汇聚',
        '团队凝聚力强','适合聚会约会','注意脾胃消化','资金汇聚适合集资'),
    ('离','乾'):('火天大有','元亨','光明普照，大有收获',
        '事业大有所成','感情丰收美满','注意心血管眼睛','财运极佳收获丰厚'),
    ('离','兑'):('火泽睽','小事吉','两力相背，求同存异',
        '意见分歧需协调','有隔阂需坦诚沟通','注意眼睛保养','投资方向有分歧'),
    ('离','离'):('离为火','利贞亨','光明附丽，文明之象',
        '展现才华适合创意','热烈浪漫不可急躁','注意心脏眼睛血液','财运明朗防内在空虚'),
    ('离','震'):('火雷噬嗑','亨利用狱','咬合之象，排除障碍',
        '阻碍需强力解决','障碍需直面解决','注意口腔牙齿','财务问题果断处理'),
    ('离','巽'):('火风鼎','元吉亨','鼎器之象，革故鼎新',
        '新机遇适合开拓','需要耐心用心经营','注意饮食营养','适合长期布局'),
    ('离','坎'):('火水未济','亨小狐汔济','功亏一篑之象',
        '即将完成不可松懈','接近成功还有考验','治疗不可半途而废','回报即将兑现耐心等待'),
    ('离','艮'):('火山旅','小亨旅贞吉','旅行之象，客居他乡',
        '有出差调动机会','异地恋聚少离多','注意水土不服','外出求财有利开支也大'),
    ('离','坤'):('火地晋','康侯用锡马蕃庶','日出地上，光明渐进',
        '升职加薪好兆头','感情稳步发展','身体日渐好转','财运渐旺'),
    ('震','乾'):('雷天大壮','利贞','壮盛之象，防过壮则折',
        '蒸蒸日上但不可骄傲','控制情绪不可强势','体力充沛防冲动受伤','资金充裕不可挥霍'),
    ('震','兑'):('雷泽归妹','征凶无攸利','不合常规需谨慎',
        '合作可能不合规范','需正视问题不可委曲求全','注意内分泌','投资有合规风险'),
    ('震','离'):('雷火丰','亨王假之','丰盛之象，鼎盛时期',
        '达到巅峰需居安思危','珍惜当下不可挥霍','状态极佳保持节制','财运旺盛见好就收'),
    ('震','震'):('震为雷','亨震来虩虩笑言哑哑','震动而起，有惊无险',
        '突发变动不必恐慌','经历考验后更坚固','注意惊吓心悸','财运有波动留应急金'),
    ('震','巽'):('雷风恒','亨无咎利贞','恒久之象，持久不变',
        '稳定发展适合长期规划','长久稳定婚姻美满','养生贵在坚持','长线投资有利'),
    ('震','坎'):('雷水解','利西南','解除之象，春雷解冻',
        '困难迎刃而解贵人相助','误会解除冰释前嫌','疾病好转注意恢复','财务困境解除'),
    ('震','艮'):('雷山小过','亨可小事不可大事','小有过越，小事可为',
        '做好分内不宜好高骛远','小浪漫有利不宜操办大事','小毛病适度保养','小额投资可以大额暂缓'),
    ('震','坤'):('雷地豫','利建侯行师','愉悦之象，万物欣悦',
        '工作氛围愉快','甜蜜快乐适合约会','心情舒畅有利健康','财运不错'),
    ('巽','乾'):('风天小畜','亨密云不雨','小有蓄积，蓄势待发',
        '积累经验厚积薄发','缘分尚需培养','调养不可急于求成','资金积累中坚持储蓄'),
    ('巽','兑'):('风泽中孚','豚鱼吉','诚信之象，感化万物',
        '以诚信立身信誉带机遇','真心换真心坦诚相待','身心和谐修心养性','信用带来财运'),
    ('巽','离'):('风火家人','利女贞','家道之象，各司其职',
        '如家人协作分工明确','以家庭为重适合婚嫁','家庭有规律利健康','家庭理财效果好'),
    ('巽','震'):('风雷益','利有攸往利涉大川','增益之象，越来越好',
        '得到支持贵人提携','收获满满共同成长','身体越来越好','财运上升收入增加'),
    ('巽','巽'):('巽为风','小亨利攸往','柔顺渗透，以柔克刚',
        '善于沟通协调','温柔体贴润物无声','注意呼吸系统','财运平稳渐进'),
    ('巽','坎'):('风水涣','亨王假有庙','涣散之象，化险为夷',
        '困局有望化解危机有转机','冷战有望改善主动沟通','精神涣散需静心','资金分散需整合'),
    ('巽','艮'):('风山渐','女归吉利贞','渐进之象，循序渐进',
        '一步一个脚印','按部就班急不得','调理需要时间','稳健投资持续增长'),
    ('巽','坤'):('风地观','盥而不荐','观察之象，以观代动',
        '先观察形势再决定','先了解不急于表白','定期体检早发现','先观望看清趋势'),
    ('坎','乾'):('水天需','有孚光亨贞吉','等待之象，待时而动',
        '机会未成熟需等待','缘分未到不必强求','恢复需要时间','时机未到持币观望'),
    ('坎','兑'):('水泽节','亨苦节不可贞','节制之象，过犹不及',
        '注意节奏劳逸结合','保持适度距离','饮食有节起居有常','理财要节制合理规划'),
    ('坎','离'):('水火既济','亨小利贞初吉终乱','已成之象，防盛极而衰',
        '项目完成不可松懈','修成正果需持续经营','身体良好继续保持','落袋为安见好就收'),
    ('坎','震'):('水雷屯','元亨利贞勿用有攸往','初生之难，万事开头难',
        '起步艰难但前景光明','刚开始有波折给时间','新调理给适应时间','初期亏损正常长线持有'),
    ('坎','巽'):('水风井','改邑不改井','井水之象，根基稳固',
        '打好基础提升核心能力','如井水深沉持久','注重根本调理养肾固本','注重基础配置'),
    ('坎','坎'):('坎为水','有孚维心亨','重重险阻，心诚可通',
        '困难较多保持信心','面临考验风雨同舟','注意肾脏泌尿系统','财运低迷谨慎投资'),
    ('坎','艮'):('水山蹇','利西南不利东北','蹇难之象，进退两难',
        '遇到瓶颈换思路','遇到阻碍先冷静','注意腿部关节','投资被套不宜加仓'),
    ('坎','坤'):('水地比','吉原筮元永贞','亲比之象，相辅相成',
        '合作运极佳众志成城','亲密和睦心有灵犀','有良医贵人','合作投资有利'),
    ('艮','乾'):('山天大畜','利贞不家食吉','大蓄之象，厚积薄发',
        '前期积累发挥作用','长期培养基础深厚','养生调理见效','长期投资开始回报'),
    ('艮','兑'):('山泽损','有孚元吉无咎','减损之象，舍小取大',
        '牺牲短期换长期','需要付出和妥协','适当做减法','短期亏损为长远布局'),
    ('艮','离'):('山火贲','亨小利有攸往','文饰之象，注重形象',
        '注重形象适当展示','注重外在也需内在','外在保养内在调理','表面不错透过现象看本质'),
    ('艮','震'):('山雷颐','贞吉观颐','颐养之象，修养身心',
        '休养生息为下阶段蓄力','相互滋养共同成长','重点调养阶段','以守为主积累资金'),
    ('艮','巽'):('山风蛊','元亨利涉大川','整治之象，拨乱反正',
        '需要整顿改革清除积弊','清理旧账坦诚面对','慢性问题需根治','账目需清理重新规划'),
    ('艮','坎'):('山水蒙','亨匪我求童蒙','启蒙之象，虚心学习',
        '需要学习新技能','需要学习和成长','学习养生知识','投资先学习不懂不投'),
    ('艮','艮'):('艮为山','艮其背不获其身','止而不动，知止而止',
        '知道什么时候该停','给对方空间不越界','及时休息','知道止盈止损'),
    ('艮','坤'):('山地剥','不利有攸往','剥落之象，阴盛阳衰',
        '低谷期不宜冒险','面临分手冷淡期','机能下降重点保养','财运低迷减少投资'),
    ('坤','乾'):('地天泰','小往大来吉亨','天地交泰，阴阳和合',
        '顺风顺水贵人相助','美满和谐天作之合','阴阳平衡最佳状态','财运极佳小投大回报'),
    ('坤','兑'):('地泽临','元亨利贞','亲临之象，好运将至',
        '有贵人关注表现机会','贵人牵线或对象主动','有良医指导','财运看好有大额机会'),
    ('坤','离'):('地火明夷','利艰贞','光明受损，韬光养晦',
        '怀才不遇需忍耐','真心被误解需时间','潜在问题需检查','财运不佳有暗亏'),
    ('坤','震'):('地雷复','亨出入无疾','一阳来复，否极泰来',
        '迎来转机困境好转','有复合回暖机会','身体开始恢复','亏损回本扭亏为盈'),
    ('坤','巽'):('地风升','元亨用见大人','上升之象，步步高升',
        '稳步上升升职有望','逐步升温水到渠成','持续改善越来越好','财运稳步上升'),
    ('坤','坎'):('地水师','贞丈人吉','统帅之象，运筹帷幄',
        '展现领导力主导项目','需要主动引导规划','健康管理需系统规划','理财需系统规划'),
    ('坤','艮'):('地山谦','亨君子有终','谦虚之象，德高望重',
        '谦虚低调赢得尊重','谦逊有礼更得人心','听从专业建议','低调投资闷声发财'),
    ('坤','坤'):('坤为地','元亨利牝马之贞','厚德载物，包容一切',
        '宜配合支持做好辅助','温柔包容以柔克刚','注意脾胃腹部保养','财运平稳稳健投资'),
}

# ============================================================
# 核心算法
# ============================================================

def num_to_trigram(n: int) -> str:
    r = n % 8
    return XIANTIAN_NUM[r if r else 8]

def num_to_yao(n: int) -> int:
    r = n % 6
    return r if r else 6

def get_dizhi_num(year: int) -> int:
    return (year - 4) % 12 + 1

def _shichen(hour: int) -> int:
    if hour >= 23 or hour < 1: return 1
    return (hour + 1) // 2 + 1

def time_method(now: datetime.datetime) -> Tuple[int,int,int]:
    yn = get_dizhi_num(now.year)
    m, d = now.month, now.day
    sc = _shichen(now.hour)
    return yn+m+d, yn+m+d+sc, yn+m+d+sc

def number_method(numbers: list) -> Tuple[int,int,int]:
    if len(numbers) == 2: return numbers[0], numbers[1], sum(numbers)
    if len(numbers) == 3: return numbers[0], numbers[1], numbers[2]
    mid = len(numbers) // 2
    return sum(numbers[:mid]), sum(numbers[mid:]), sum(numbers)

def char_method(text: str) -> Tuple[int,int,int]:
    chars = list(text.strip())
    n = len(chars) * 5
    if len(chars) <= 2: return n//2, n-n//2, n
    mid = len(chars) // 2
    return mid*5, (len(chars)-mid)*5, n

def build_lines(upper: str, lower: str) -> list:
    return TRIGRAM_BITS[lower] + TRIGRAM_BITS[upper]

def derive_hu(lines: list) -> Tuple[str,str]:
    return BITS_TO_TRIGRAM.get(tuple(lines[2:5]),'坤'), BITS_TO_TRIGRAM.get(tuple(lines[1:4]),'坤')

def derive_bian(lines: list, dong: int) -> Tuple[str,str]:
    b = lines.copy()
    b[dong-1] = 1 - b[dong-1]
    return BITS_TO_TRIGRAM.get(tuple(b[3:6]),'坤'), BITS_TO_TRIGRAM.get(tuple(b[0:3]),'坤')

def determine_tiyong(dong: int, upper: str, lower: str) -> Tuple[str,str]:
    return (upper, lower) if dong <= 3 else (lower, upper)

def analyze_wuxing(ti: str, yong: str) -> dict:
    if ti == yong:
        return {'relation':'比和','level':'吉','desc':f'体用皆为{ti}，比和之象，事可顺遂'}
    if WUXING_SHENG.get(yong) == ti:
        return {'relation':f'{yong}生{ti}','level':'吉','desc':f'用卦{yong}生体卦{ti}，外力助我，所求皆遂'}
    if WUXING_SHENG.get(ti) == yong:
        return {'relation':f'{ti}生{yong}','level':'平偏凶','desc':f'体卦{ti}生用卦{yong}，精力外泄，需防过劳'}
    if WUXING_KE.get(ti) == yong:
        return {'relation':f'{ti}克{yong}','level':'平','desc':f'体卦{ti}克用卦{yong}，虽能制之但耗费气力'}
    if WUXING_KE.get(yong) == ti:
        return {'relation':f'{yong}克{ti}','level':'凶','desc':f'用卦{yong}克体卦{ti}，外力制我，宜退守不宜冒进'}
    return {'relation':'未知','level':'平','desc':''}

def wangshuai(element: str, month: int) -> str:
    me = MONTH_WANGLING.get(month, '土')
    if element == me: return '旺'
    if WUXING_SHENG.get(me) == element: return '相'
    if WUXING_SHENG.get(element) == me: return '休'
    if WUXING_KE.get(me) == element: return '死'
    return '囚'

def timing(ti_element: str, dong: int) -> str:
    t = {'金':'秋季（申酉月，约8-10月）或申酉日','木':'春季（寅卯月，约2-4月）或寅卯日',
         '水':'冬季（亥子月，约11-1月）或亥子日','火':'夏季（巳午月，约5-7月）或巳午日',
         '土':'四季末（辰戌丑未月）或辰戌丑未日'}
    return f'应期约在{t.get(ti_element,"近期")}，数理暗示{dong}日内或{dong}周内可见分晓。'

# ============================================================
# 主函数
# ============================================================

def divine(question: str, method='time', numbers=None, text=None, now=None) -> dict:
    if now is None: now = datetime.datetime.now()

    if method == 'number' and numbers:
        un, ln, dn = number_method(numbers)
    elif method == 'char' and text:
        un, ln, dn = char_method(text)
    else:
        un, ln, dn = time_method(now)

    upper = num_to_trigram(un)
    lower = num_to_trigram(ln)
    dong = num_to_yao(dn)

    lines = build_lines(upper, lower)
    ti, yong = determine_tiyong(dong, upper, lower)
    ti_el, yong_el = TRIGRAM_ATTR[ti]['element'], TRIGRAM_ATTR[yong]['element']

    hu_u, hu_l = derive_hu(lines)
    bian_u, bian_l = derive_bian(lines, dong)

    month = now.month
    ti_ws = wangshuai(ti_el, month)
    yong_ws = wangshuai(yong_el, month)
    wx = analyze_wuxing(ti_el, yong_el)

    ben = HEX.get((upper, lower), HEX[('坤','坤')])
    hu = HEX.get((hu_u, hu_l), HEX[('坤','坤')])
    bian = HEX.get((bian_u, bian_l), HEX[('坤','坤')])

    # Overall
    if ti_ws in ('旺','相') and wx['level'] == '吉':
        tone = '大吉之象'
    elif ti_ws == '旺' and wx['level'] != '凶':
        tone = '吉象'
    elif ti_ws in ('死','囚') and wx['level'] == '凶':
        tone = '不利之象'
    elif ti_ws in ('旺','相') and wx['level'] == '凶':
        tone = '有惊无险'
    elif ti_ws in ('死','囚') and wx['level'] == '吉':
        tone = '心有余力不足'
    else:
        tone = wx['level']

    overall = f'【{tone}】{wx["desc"]}\n本卦{ben[0]}，卦辞「{ben[1]}」。{ben[2]}。'

    advice = _advice(ti, yong, ti_el, yong_el, wx, ben, bian)

    result = {
        'question': question,
        'timestamp': now.strftime('%Y-%m-%d %H:%M:%S'),
        'method': method,
        'ben_hex': {'name':ben[0],'brief':ben[1],'judgment':ben[2],'lines':lines,'dong_yao':dong,
                     'upper':upper,'lower':lower,
                     'upper_attr':TRIGRAM_ATTR[upper],'lower_attr':TRIGRAM_ATTR[lower]},
        'hu_hex': {'name':hu[0],'brief':hu[1],'judgment':hu[2],'upper':hu_u,'lower':hu_l,
                    'upper_attr':TRIGRAM_ATTR[hu_u],'lower_attr':TRIGRAM_ATTR[hu_l]},
        'bian_hex': {'name':bian[0],'brief':bian[1],'judgment':bian[2],'upper':bian_u,'lower':bian_l,
                      'upper_attr':TRIGRAM_ATTR[bian_u],'lower_attr':TRIGRAM_ATTR[bian_l]},
        'ti': {'gua':ti,'element':ti_el,'nature':TRIGRAM_ATTR[ti]['nature'],
               'image':TRIGRAM_ATTR[ti]['image'],'wangshuai':ti_ws},
        'yong': {'gua':yong,'element':yong_el,'nature':TRIGRAM_ATTR[yong]['nature'],
                 'image':TRIGRAM_ATTR[yong]['image'],'wangshuai':yong_ws},
        'wuxing': {'relation':wx['relation'],'level':wx['level'],'desc':wx['desc']},
        'prediction': {
            'overall': overall,
            'career': ben[3], 'love': ben[4], 'finance': ben[6], 'health': ben[5],
            'advice': advice,
            'timing': timing(ti_el, dong),
        },
    }
    return result


def _advice(ti, yong, ti_el, yong_el, wx, ben, bian):
    parts = []
    if wx['level'] == '吉':
        parts.append(f'当前{ti}卦当令，{TRIGRAM_ATTR[ti]["image"]}，宜主动出击。')
    elif wx['level'] == '凶':
        parts.append(f'用卦{yong}({yong_el})克体卦{ti}({ti_el})，宜退守等待，以静制动。')
    else:
        parts.append(f'体用平稳，{ben[0]}提示按部就班，稳中求进。')
    if bian[0] != ben[0]:
        parts.append(f'变卦{bian[0]}暗示最终走向：{bian[2]}。')
    ea = {'金':'宜穿白色银色，方位利西北','木':'宜穿绿色青色，方位利东方',
          '水':'宜穿黑色蓝色，方位利北方','火':'宜穿红色紫色，方位利南方',
          '土':'宜穿黄色棕色，方位利中央'}
    parts.append(f'五行调理：体卦{ti_el}，{ea.get(ti_el,"")}。')
    return ''.join(parts)


def add_premium(result: dict, now: datetime.datetime) -> dict:
    """Premium: 流年 + 深度建议"""
    year = now.year
    dizhi = DIZHI[(year-4)%12]
    DIZHI_WX = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火',
                '午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
    ywx = DIZHI_WX[dizhi]
    twx = result['ti']['element']
    if ywx == twx: s = f'{year}{dizhi}年，流年{ywx}与体卦{twx}比和，运势平稳。'
    elif WUXING_SHENG.get(ywx) == twx: s = f'{year}{dizhi}年，流年{ywx}生体卦{twx}，得岁运之助，运势上扬。'
    elif WUXING_SHENG.get(twx) == ywx: s = f'{year}{dizhi}年，体卦{twx}生流年{ywx}，泄气之年，付出多回报需等。'
    elif WUXING_KE.get(ywx) == twx: s = f'{year}{dizhi}年，流年{ywx}克体卦{twx}，受岁运压制，宜守不宜攻。'
    else: s = f'{year}{dizhi}年，体卦{twx}克流年{ywx}，虽可制之但需耗力。'
    result['yearly'] = {'year':year,'dizhi':dizhi,'year_wuxing':ywx,'analysis':s}

    ti, yong, wx = result['ti'], result['yong'], result['wuxing']
    ben, hu, bian = result['ben_hex'], result['hu_hex'], result['bian_hex']
    deep = []
    if wx['level'] == '吉':
        deep.append(f'【行动】{ti["gua"]}卦{ti["image"]}，宜主动出击。用卦{yong["gua"]}生助体卦，外部条件有利。')
    elif wx['level'] == '凶':
        deep.append(f'【行动】用卦{yong["gua"]}({yong["element"]})克体卦{ti["gua"]}({ti["element"]})，宜退守。')
    else:
        deep.append(f'【行动】体用平稳，按部就班。')
    deep.append(f'【过程】互卦{hu["name"]}（{hu["brief"]}）暗示过程中会经历{TRIGRAM_ATTR[hu["upper"]]["image"]}的阶段。')
    deep.append(f'【趋势】变卦{bian["name"]}（{bian["brief"]}）为最终走向。')
    result['deep_advice'] = '\n'.join(deep)
    return result


# ============================================================
# CLI
# ============================================================

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='梅花易数专业起卦')
    p.add_argument('--query', '-q', required=True, help='所问事项')
    p.add_argument('--method', '-m', default='time', choices=['time','number','char'])
    p.add_argument('--numbers', '-n', type=int, nargs='+', help='报数 (如 3 7)')
    p.add_argument('--text', '-t', help='字数起卦文字')
    p.add_argument('--tier', default='detailed', choices=['basic','detailed','premium'])
    args = p.parse_args()

    result = divine(args.query, method=args.method, numbers=args.numbers, text=args.text)

    if args.tier == 'basic':
        out = {k:result[k] for k in ['question','timestamp','ben_hex','ti','yong','wuxing']}
        out['prediction'] = {'overall':result['prediction']['overall'],'advice':result['prediction']['advice']}
    elif args.tier == 'premium':
        out = add_premium(result, datetime.datetime.now())
    else:
        out = result

    out['tier'] = args.tier
    print(json.dumps(out, ensure_ascii=False, indent=2))
