#!/usr/bin/env python3
"""评估业务材料完整度；结合深度业务模型，避免出现“0/0 但无待确认项”。"""
from __future__ import annotations
import argparse, json, re, sys, zipfile
from pathlib import Path

DOMAIN_TOPICS={
 'pointwork': {
   '人员唯一标识':['工号','员工','姓名'], '组织/线别/班组':['线别','班组','组织','部门'], '考勤周期':['考勤周期','26日','25日','自然月'],
   '排班/班时':['排班','班时','班次'], '正工/加班':['正工','加班','工时'], '请假/借调/支援':['请假','借调','支援','跨线'],
   '打卡核对':['打卡','刷卡','考勤机'], '审核/锁定':['审核','审批','锁定','确认'], '正式导出模板':['日报','月报','签字','合计']},
 'energy': {
   '能源类型/表计':['能源','用电','用水','天然气','蒸汽','表计','抄表'], '组织/产线':['工厂','课别','产线','线别'], '日期/月度归属':['日期','月份','周期'],
   '起止值/用量':['起始','终止','用量','读数'], '产量/单耗':['产量','单耗'], '目标/标准':['目标','标准'],
   '同比/环比/方向':['同比','环比','达成','越低','越高'], '确认/审核':['确认','审核','审批'], '正式导出模板':['日报','月报','签字','合计']},
 'operations': {
   '线别/班次/班时':['线别','班次','班时'], '产品/规格':['产品','品项','规格'], '人工工时':['人工工时','制造人工','包装人工'],
   '机器工时':['机器工时'], '损耗/化学品/能耗':['原料损耗','物料损耗','化学品','油品','能耗'], '动态字段':['动态字段','字段类别','字段项','两级表头'],
   '签字/审核':['签字','审核','审批','经办'], '历史字段迁移':['历史字段','旧字段','迁移','映射'], '正式导出模板':['运营记录','日报','签字','合计']},
 'production': {
   '工单/计划唯一标识':['工单','计划号','批次','编号'], '产品/规格':['产品','品项','规格'], '产线/班组':['产线','班组','线别'], '计划与完成量':['计划数量','完成数量','产量'],
   '生产日期/班次':['生产日期','日期','班次'], '状态/报工':['报工','状态','完工'], '审核/确认':['审核','确认','审批'], '导出/报表':['日报','生产报表','合计']},
 'quality': {
   '检验单/批次':['检验单','批次','编号'], '检验项目/标准':['检验项目','质量标准','标准'], '结果':['合格','不合格','结果'], '抽检/样本':['抽检','样本','数量'],
   '整改/复验':['整改','复验'], '责任/人员':['责任人','检验员','人员'], '审核':['审核','审批','确认'], '质量报表':['质量报表','日报','合计']},
 'equipment': {
   '设备唯一标识':['设备编号','设备编码','设备名称'], '点检':['点检','巡检'], '维修/故障':['维修','故障','停机'], '保养':['保养','维保'],
   '备件':['备件','配件'], '时间/周期':['日期','周期','时间'], '责任人':['责任人','维修人','人员'], '设备报表':['设备报表','日报','合计']},
 'inventory': {
   '物料唯一标识':['物料编码','物料编号','SKU','品号'], '仓库/库位':['仓库','库位'], '入库':['入库','收货'], '出库':['出库','领料'],
   '库存数量':['库存量','库存数量','结存'], '批次/效期':['批次','效期'], '盘点':['盘点','差异'], '库存报表':['库存报表','台账','合计']},
 'approval': {
   '申请单唯一标识':['申请单','单号','编号'], '申请人/部门':['申请人','部门'], '申请内容':['申请事项','内容','原因'], '状态':['待审批','批准','退回','状态'],
   '审批人/节点':['审批人','审核人','节点'], '审批顺序':['审批顺序','流程','一级','二级'], '时间':['申请时间','审批时间','日期'], '审批记录':['审批记录','意见','签核']},
 'general': {
   '业务对象与字段':['字段','表头','列','名称'], '业务唯一键':['编号','编码','单号','ID','工号'], '计算规则':['公式','计算','合计','比例'], '状态/流程':['状态','流程','审批','审核'],
   '角色/权限':['角色','权限','管理员','用户'], '查询/筛选':['查询','筛选','搜索'], '导入导出':['导入','导出','Excel'], '统计/报表':['统计','报表','看板']}
}
TEXT_EXT={'.txt','.md','.csv','.tsv','.json','.yaml','.yml'}
TABULAR_EXT={'.xlsx','.xlsm','.xls','.csv','.tsv','.json'}
RULE_EXT={'.docx','.doc','.pdf','.md','.txt'}
CODE_MARKERS={'.py','.sql','.db','.sqlite','.html','.js','.css'}


def iter_files(source):
    if source.is_file(): yield source; return
    for p in source.rglob('*'):
        if p.is_file() and not p.is_symlink() and '__MACOSX' not in p.parts and not p.name.startswith('~$'): yield p


def decode(raw):
    for enc in ('utf-8-sig','utf-8','gb18030'):
        try:return raw.decode(enc)
        except UnicodeDecodeError: pass
    return ''


def extract_text(p):
    parts=[p.name]; suf=p.suffix.lower()
    try:
        if suf in TEXT_EXT: parts.append(decode(p.read_bytes()[:500000]))
        elif suf in {'.xlsx','.xlsm','.docx','.zip'}:
            with zipfile.ZipFile(p) as z:
                names=[i.filename for i in z.infolist() if not i.is_dir()][:3000]; parts.append(' '.join(names))
                for name in names:
                    if name.endswith(('sharedStrings.xml','workbook.xml','document.xml')):
                        try: parts.append(re.sub(r'<[^>]+>',' ',decode(z.read(name)[:700000])))
                        except Exception: pass
    except Exception: pass
    return '\n'.join(parts)


def classify_materials(files,model):
    has_tabular=bool(model.get('business_objects')) or any(p.suffix.lower() in TABULAR_EXT for p in files)
    has_rules=any(p.suffix.lower() in RULE_EXT for p in files) or bool(model.get('calculation_rules'))
    has_source=False; source_evidence=[]
    for p in files:
        if p.suffix.lower() in CODE_MARKERS: has_source=True; source_evidence.append(p.name)
        elif p.suffix.lower()=='.zip':
            try:
                with zipfile.ZipFile(p) as z:
                    names=[Path(i.filename).suffix.lower() for i in z.infolist() if not i.is_dir()][:5000]
                    if sum(s in CODE_MARKERS for s in names)>=3: has_source=True; source_evidence.append(p.name)
            except Exception: pass
    if has_source and has_rules and has_tabular: grade='A'
    elif has_tabular and (has_rules or has_source): grade='B'
    elif has_tabular: grade='C'
    else: grade='D'
    return grade,{'tabular_or_history':has_tabular,'rules_or_formal_docs':has_rules,'existing_source_or_database':has_source,'source_evidence':source_evidence}


def model_text(model):
    parts=[]
    for o in model.get('business_objects',[]):
        parts.append(str(o.get('label',''))); parts.extend(str(f.get('label','')) for f in o.get('fields',[]))
    for r in model.get('calculation_rules',[]): parts.extend([str(r.get('target_label','')),str(r.get('original_formula',''))])
    for e in model.get('text_evidence',[]): parts.append(str(e.get('text','')))
    return '\n'.join(parts)


def assess(source,profile,model):
    files=list(iter_files(source)); combined=('\n'.join(extract_text(p) for p in files)+'\n'+model_text(model)).lower()
    grade,materials=classify_materials(files,model)
    topics=DOMAIN_TOPICS.get(profile) or DOMAIN_TOPICS['general']
    # composite 使用通用门禁，避免多个域合并时出现 0/0。
    if profile=='composite': topics=DOMAIN_TOPICS['general']
    topic_results=[]
    for topic,kws in topics.items():
        hits=[k for k in kws if k.lower() in combined]
        # 结构本身也是证据，不要求文档恰好出现“字段/表头”字样。
        structural=False
        if topic=='业务对象与字段' and model.get('business_objects'): structural=True
        if topic=='业务唯一键' and any(o.get('unique_key_candidates') for o in model.get('business_objects',[])): structural=True
        if topic=='计算规则' and model.get('calculation_rules'): structural=True
        topic_results.append({'topic':topic,'evidence_found':bool(hits) or structural,'keywords':hits[:8], 'evidence_type':'structure' if structural and not hits else 'text_or_structure'})
    found=sum(x['evidence_found'] for x in topic_results)
    return {'schema_version':'1.1','profile':profile,'grade':grade,'materials':materials,'topic_coverage':{'found':found,'total':len(topic_results)},'topics':topic_results,
            'model_summary':model.get('summary',{}),'policy':'无证据支持的关键周期、公式、目标方向、审核、权限和唯一键不得静默猜测；应写入 ASSUMPTIONS.md 或 BUSINESS_CONFLICTS.md。'}


def render(obj):
    g=obj['grade']; m=obj['materials']; c=obj['topic_coverage']
    meaning={'A':'结构化数据 + 规则材料 + 现有源码/数据库证据较完整，适合继承式升级或高完整度生成。','B':'有结构化业务数据，并存在规则材料或现有源码证据；仍需核对未覆盖关键规则。','C':'主要只有结构化报表/模板；可自动生成字段、录入、查询、导入导出等，但关键规则不得自动补齐。','D':'缺少可验证的结构化业务材料；只能生成通用原型/骨架，不能宣称已还原正式业务口径。'}[g]
    ms=obj.get('model_summary',{})
    lines=['# INPUT_COMPLETENESS_REPORT','',f'- 业务 Profile：**{obj["profile"]}**',f'- 资料完整度：**{g}级**',f'- 关键主题证据覆盖：**{c["found"]}/{c["total"]}**',f'- 已提取业务对象/字段：**{ms.get("structured_objects",0)}/{ms.get("fields",0)}**',f'- 判定说明：{meaning}','','## 材料结构','',f'- 结构化报表/历史数据：{"✓" if m["tabular_or_history"] else "×"}',f'- 制度/规则/正式文档：{"✓" if m["rules_or_formal_docs"] else "×"}',f'- 现有源码/数据库证据：{"✓" if m["existing_source_or_database"] else "×"}','','## 关键主题证据','']
    for x in obj['topics']:
        mark='✓' if x['evidence_found'] else '△'; detail='、'.join(x['keywords']) if x['keywords'] else ('来自结构化模型' if x.get('evidence_type')=='structure' else '未发现直接证据')
        lines.append(f'- {mark} **{x["topic"]}**：{detail}')
    lines += ['','## 生成策略','',obj['policy'],'','> 本报告是“资料是否足以支撑正式规则”的风险提示，不代表业务内容已经被人工确认。','']
    return '\n'.join(lines)


def main():
    ap=argparse.ArgumentParser(description='评估业务资料完整度并生成 INPUT_COMPLETENESS_REPORT。')
    ap.add_argument('source'); ap.add_argument('--profile',required=True); ap.add_argument('--model',default=None); ap.add_argument('--output',default='INPUT_COMPLETENESS_REPORT.md'); ap.add_argument('--json-output',default=None)
    a=ap.parse_args(); src=Path(a.source)
    if not src.exists(): print('[PB001] 输入路径不存在'); return 1
    model={}
    if a.model:
        try:model=json.loads(Path(a.model).read_text(encoding='utf-8'))
        except Exception: model={}
    if not model:
        try:
            from extract_business_model import build_model
            model=build_model(src)
        except Exception:model={}
    obj=assess(src,a.profile,model); Path(a.output).write_text(render(obj),encoding='utf-8')
    if a.json_output: Path(a.json_output).write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')
    print(f'[完成] 资料完整度：{obj["grade"]}级，主题证据 {obj["topic_coverage"]["found"]}/{obj["topic_coverage"]["total"]}')
    return 0
if __name__=='__main__': sys.exit(main())
