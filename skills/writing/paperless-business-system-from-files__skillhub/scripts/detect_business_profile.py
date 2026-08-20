#!/usr/bin/env python3
"""只读识别业务域候选，并生成可解释的业务识别证据。

本脚本只负责“路由证据”，不替代用户当前要求、正式制度、表单或现有源码。
"""
from __future__ import annotations
import argparse, json, re, sys, zipfile
from collections import defaultdict
from pathlib import Path
from xml.etree import ElementTree as ET

DOMAINS = {
    "energy": ["能源","能耗","用电","电量","用水","水量","天然气","蒸汽","压缩空气","抄表","表计","单耗","目标达成"],
    "operations": ["运营记录","人工工时","机器工时","原料损耗","物料损耗","化学品/油品","制造人工","包装人工","品项切换人工","夹赠工时"],
    "pointwork": ["点工","考勤","工号","排班","班时","正工","加班","请假","打卡","借调","非生产工时","实际出勤"],
    "production": ["生产计划","工单","报工","产量","产线","班组","计划数量","完成数量"],
    "quality": ["质量","检验","合格","不合格","整改","复验","质量标准","抽检"],
    "equipment": ["设备","点检","维修","保养","故障","停机","设备编号","备件"],
    "inventory": ["库存","物料","入库","出库","仓库","盘点","库存量","批次"],
    "approval": ["审批","审核","申请单","退回","待审批","批准","签核"],
}
TEXT_EXT={".txt",".md",".csv",".tsv",".json",".yaml",".yml"}


def add_text(scores,evidence,text,weight,source):
    low=text.lower()
    for domain, kws in DOMAINS.items():
        hits=[]
        for kw in kws:
            n=low.count(kw.lower())
            if n:
                points=min(n,5)*weight
                scores[domain]+=points
                hits.append({"keyword":kw,"count":min(n,5),"points":points})
        if hits:
            evidence[domain].append({"source":source,"hits":hits[:10],"weight":weight})


def read_text(path,limit=300000):
    raw=path.read_bytes()[:limit]
    for enc in ("utf-8-sig","utf-8","gb18030"):
        try:return raw.decode(enc)
        except UnicodeDecodeError:pass
    return ""


def inspect_xlsx(path,scores,evidence):
    try:
        with zipfile.ZipFile(path) as z:
            if "xl/workbook.xml" in z.namelist():
                root=ET.fromstring(z.read("xl/workbook.xml"))
                ns={"m":"http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
                sheets=[s.attrib.get("name","") for s in root.findall(".//m:sheet",ns)]
                add_text(scores,evidence," ".join(sheets),3,f"{path.name}:sheet_names")
            if "xl/sharedStrings.xml" in z.namelist():
                data=z.read("xl/sharedStrings.xml")[:800000]
                try:
                    node=ET.fromstring(data)
                    text=" ".join(t.text or "" for t in node.iter() if t.tag.endswith('}t'))
                    add_text(scores,evidence,text,1,f"{path.name}:shared_strings")
                except ET.ParseError:
                    pass
    except (OSError,zipfile.BadZipFile):
        pass


def inspect_docx(path,scores,evidence):
    try:
        with zipfile.ZipFile(path) as z:
            if "word/document.xml" in z.namelist():
                data=z.read("word/document.xml")[:800000]
                text=re.sub(r"<[^>]+>"," ",data.decode("utf-8","ignore"))
                add_text(scores,evidence,text,1,f"{path.name}:document")
    except (OSError,zipfile.BadZipFile):
        pass


def inspect_zip(path,scores,evidence):
    try:
        with zipfile.ZipFile(path) as z:
            names=[i.filename for i in z.infolist() if not i.is_dir()][:5000]
            add_text(scores,evidence," ".join(names),3,f"{path.name}:member_names")
            for i in z.infolist()[:5000]:
                if i.is_dir() or i.file_size > 300000:
                    continue
                suf=Path(i.filename).suffix.lower()
                if suf in TEXT_EXT:
                    try:
                        raw=z.read(i)[:300000]
                        text=""
                        for enc in ("utf-8-sig","utf-8","gb18030"):
                            try: text=raw.decode(enc); break
                            except UnicodeDecodeError: pass
                        if text: add_text(scores,evidence,text,1,f"{path.name}:{i.filename}")
                    except Exception:
                        pass
    except (OSError,zipfile.BadZipFile):
        pass


def iter_files(source):
    if source.is_file(): yield source; return
    for p in source.rglob('*'):
        if p.is_file() and not p.is_symlink() and '__MACOSX' not in p.parts and not p.name.startswith('~$'):
            yield p


def confidence_score(positive):
    if not positive: return 0
    top=positive[0][1]
    second=positive[1][1] if len(positive)>1 else 0
    absolute=min(60, top*3)
    separation=40 if second==0 else max(0, min(40, round((top-second)/max(top,1)*40)))
    return max(1,min(99,int(absolute+separation)))


def flatten_reason(domain_evidence,limit=8):
    reasons=[]
    seen=set()
    for item in domain_evidence:
        for hit in item.get('hits',[]):
            key=(hit['keyword'],item['source'])
            if key in seen: continue
            seen.add(key)
            reasons.append({"keyword":hit['keyword'],"source":item['source'],"points":hit['points']})
            if len(reasons)>=limit: return reasons
    return reasons


def detect(source, model_path=None):
    scores=defaultdict(int); evidence=defaultdict(list)
    file_count=0
    for p in iter_files(source):
        file_count+=1
        add_text(scores,evidence,p.name,4,f"filename:{p.name}")
        suf=p.suffix.lower()
        if suf in TEXT_EXT:
            add_text(scores,evidence,read_text(p),1,f"content:{p.name}")
        elif suf in {'.xlsx','.xlsm'}:
            inspect_xlsx(p,scores,evidence)
        elif suf=='.docx':
            inspect_docx(p,scores,evidence)
        elif suf=='.zip':
            inspect_zip(p,scores,evidence)
    # 深度业务模型提供比文件名/共享字符串更可靠的字段、对象和正文证据。
    model=None
    if model_path:
        try: model=json.loads(Path(model_path).read_text(encoding='utf-8'))
        except Exception: model=None
    if model is None:
        try:
            from extract_business_model import build_model
            model=build_model(source)
        except Exception:
            model=None
    if model:
        parts=[]
        for obj in model.get('business_objects',[]):
            parts.append(str(obj.get('label','')))
            parts.extend(str(f.get('label','')) for f in obj.get('fields',[]))
        for ev in model.get('text_evidence',[]): parts.append(str(ev.get('text',''))[:30000])
        add_text(scores,evidence,' '.join(parts),4,'business_model:objects_fields_text')
        for rule in model.get('calculation_rules',[]):
            add_text(scores,evidence,str(rule.get('target_label',''))+' '+str(rule.get('original_formula','')),2,'business_model:formula')
    ranked=sorted(scores.items(),key=lambda x:(-x[1],x[0]))
    positive=[x for x in ranked if x[1]>0]
    conf_score=confidence_score(positive)
    if not positive:
        final='general'; confidence='low'; strong=[]
    else:
        top=positive[0][1]
        strong=[d for d,s in positive if s>=max(5,top*0.60)]
        final='composite' if len(strong)>=2 else positive[0][0]
        confidence='high' if conf_score>=75 else ('medium' if conf_score>=45 else 'low')
    ranked_domains=[]
    for d,s in ranked:
        if s<=0: continue
        ranked_domains.append({
            "domain":d,"score":s,
            "evidence":evidence[d][:10],
            "top_reasons":flatten_reason(evidence[d],6),
        })
    return {
        "schema_version":"1.2",
        "detector_is_advisory":True,
        "source_file_count":file_count,
        "recommended_profile":final,
        "confidence":confidence,
        "confidence_score":conf_score,
        "strong_domains":strong,
        "ranked_domains":ranked_domains,
        "instruction":"最终业务结论必须结合用户当前提示词、正式规则、表单、历史数据与现有源码；本结果不得覆盖明确业务事实。"
    }


def report_markdown(obj):
    profile=obj['recommended_profile']
    lines=[
        '# BUSINESS_RECOGNITION_REPORT', '',
        f'- 推荐业务 Profile：**{profile}**',
        f'- 识别置信度：**{obj["confidence_score"]}%（{obj["confidence"]}）**',
        f'- 已盘点文件数：**{obj.get("source_file_count",0)}**',
        '- 说明：该识别结果是路由证据，不覆盖用户当前明确要求、正式制度、表单或已有系统源码。', '',
        '## 主要识别依据', ''
    ]
    ranked=obj.get('ranked_domains',[])
    if ranked:
        for idx,r in enumerate(ranked[:5],1):
            lines.append(f'### {idx}. {r["domain"]}（得分 {r["score"]}）')
            reasons=r.get('top_reasons',[])
            if reasons:
                for x in reasons:
                    lines.append(f'- `{x["keyword"]}`：来自 `{x["source"]}`，证据分 {x["points"]}')
            else:
                lines.append('- 未提取到可展示的关键词证据。')
            lines.append('')
    else:
        lines += ['- 未识别到足够的领域特征，建议按 `general` 建模，并把关键规则列入待确认项。','']
    lines += ['## 路由结论', '']
    if profile=='composite':
        lines.append('多个业务域证据同时较强，建议生成模块化组合系统；在 `system-spec.json` 中逐模块定义字段、公式、权限和流程。')
    elif profile=='general':
        lines.append('证据不足以稳定归类到已知 Profile。使用通用骨架，但不得把参考系统公式或审批规则作为默认事实。')
    else:
        lines.append(f'优先使用 `{profile}` Profile 作为工程与识别参考；真实字段、公式、周期、权限、审核和报表仍以本次附件事实为准。')
    lines += ['', '## 候选对比', '', '| 候选域 | 得分 |', '|---|---:|']
    for r in ranked[:8]: lines.append(f'| {r["domain"]} | {r["score"]} |')
    lines += ['', '> 不应把本报告中的“置信度”解释为业务规则正确率；关键规则仍需从正式资料中确认。','']
    return '\n'.join(lines)


def main():
    ap=argparse.ArgumentParser(description='只读识别业务 Profile，并可输出可解释识别报告。')
    ap.add_argument('source'); ap.add_argument('--output',default='business-profile.json'); ap.add_argument('--report',default=None); ap.add_argument('--model',default=None)
    a=ap.parse_args(); src=Path(a.source)
    if not src.exists(): print('[PB001] 输入路径不存在'); return 1
    out=detect(src,a.model); Path(a.output).write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
    if a.report: Path(a.report).write_text(report_markdown(out),encoding='utf-8')
    print(f"[完成] 推荐业务 Profile：{out['recommended_profile']}，置信度：{out['confidence_score']}%（{out['confidence']}）")
    return 0
if __name__=='__main__': sys.exit(main())
