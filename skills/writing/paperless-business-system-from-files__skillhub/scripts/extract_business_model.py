#!/usr/bin/env python3
"""从业务资料中提取可追溯的结构化业务模型。

目标不是猜业务规则，而是把“文件 -> 表/对象 -> 字段 -> 公式 -> 关系 -> 证据”显式化，
为 system-spec 和后续自动生成提供稳定输入。
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

TEXT_ENCODINGS=("utf-8-sig","utf-8","gb18030")
NS_MAIN="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
NS_REL="http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_PKG_REL="http://schemas.openxmlformats.org/package/2006/relationships"


def decode(raw:bytes)->str:
    for enc in TEXT_ENCODINGS:
        try:return raw.decode(enc)
        except UnicodeDecodeError:pass
    return raw.decode("utf-8","ignore")


def norm_label(value:Any)->str:
    s=re.sub(r"\s+"," ",str(value or "").strip())
    return s[:120]


def excel_col_index(ref:str)->int:
    m=re.match(r"([A-Z]+)",ref.upper())
    if not m:return 0
    n=0
    for ch in m.group(1):n=n*26+(ord(ch)-64)
    return n


def excel_col_name(index:int)->str:
    s=""
    while index>0:
        index,rem=divmod(index-1,26); s=chr(65+rem)+s
    return s


def normalize_headers(values:list[Any])->list[str]:
    out=[]; seen=Counter()
    for i,v in enumerate(values,1):
        base=norm_label(v) or f"未命名列{i}"
        seen[base]+=1
        out.append(base if seen[base]==1 else f"{base}__重复{seen[base]}")
    return out


def infer_scalar_type(v:Any)->str:
    if v is None or str(v).strip()=="":return "empty"
    s=str(v).strip()
    if s.lower() in {"true","false","是","否","yes","no"}:return "boolean"
    if re.fullmatch(r"[-+]?\d+",s):return "integer"
    if re.fullmatch(r"[-+]?(?:\d+\.\d*|\d*\.\d+)(?:[eE][-+]?\d+)?",s):return "number"
    if re.fullmatch(r"\d{4}[-/.年]\d{1,2}[-/.月]\d{1,2}日?",s):return "date"
    if re.fullmatch(r"\d{4}[-/.]\d{1,2}[-/.]\d{1,2}[ T]\d{1,2}:\d{2}(?::\d{2})?",s):return "datetime"
    return "text"


def infer_field_type(label:str,values:list[Any])->str:
    lab=label.lower()
    non=[v for v in values if v not in (None,"")]
    if any(k in lab for k in ("日期","年月日","date")):return "date"
    if any(k in lab for k in ("时间","时刻","datetime","time")):return "datetime"
    if any(k in lab for k in ("金额","单价","数量","工时","产量","用量","读数","单耗","比例","率","目标","数值","重量","体积","库存")):
        return "number"
    kinds=Counter(infer_scalar_type(v) for v in non[:200])
    if not kinds:return "text"
    if kinds["text"]:return "text"
    if kinds["datetime"]:return "datetime"
    if kinds["date"] and not (kinds["integer"] or kinds["number"]):return "date"
    if kinds["number"]:return "number"
    if kinds["integer"]:return "integer"
    if kinds["boolean"]:return "boolean"
    return "text"


def header_score(row:list[Any])->float:
    vals=[norm_label(v) for v in row]
    non=[v for v in vals if v]
    if len(non)<2:return -1
    text=sum(infer_scalar_type(v)=="text" for v in non)
    uniq=len(set(non))
    return len(non)*2 + text*1.5 + uniq/len(non)


def choose_header_row(rows:list[dict[int,dict[str,Any]]])->int:
    candidates=[]
    for idx,row in enumerate(rows[:15],1):
        maxc=max(row.keys(),default=0)
        vals=[row.get(c,{}).get("value","") for c in range(1,maxc+1)]
        candidates.append((header_score(vals),idx))
    # 分数相同时优先更早的行，避免纯文本数据行与表头同分时误选最后一行。
    candidates.sort(key=lambda x:(-x[0],x[1]))
    return candidates[0][1] if candidates and candidates[0][0]>=0 else 1


def shared_strings(z:zipfile.ZipFile)->list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():return []
    try:root=ET.fromstring(z.read("xl/sharedStrings.xml"))
    except ET.ParseError:return []
    out=[]
    for si in root.findall(f".//{{{NS_MAIN}}}si"):
        out.append("".join(t.text or "" for t in si.iter() if t.tag.endswith("}t")))
    return out


def workbook_sheet_targets(z:zipfile.ZipFile)->list[tuple[str,str]]:
    wb=ET.fromstring(z.read("xl/workbook.xml"))
    rels={}
    rel_path="xl/_rels/workbook.xml.rels"
    if rel_path in z.namelist():
        rr=ET.fromstring(z.read(rel_path))
        for r in rr.findall(f".//{{{NS_PKG_REL}}}Relationship"):
            rels[r.attrib.get("Id","")]=r.attrib.get("Target","")
    out=[]
    for s in wb.findall(f".//{{{NS_MAIN}}}sheet"):
        name=s.attrib.get("name","")
        rid=s.attrib.get(f"{{{NS_REL}}}id","")
        target=rels.get(rid,"")
        if target:
            target=target.lstrip("/")
            if not target.startswith("xl/"):target="xl/"+target
            target=str(Path(target).as_posix())
        out.append((name,target))
    return out


def parse_xlsx_cell(c:ET.Element,strings:list[str])->dict[str,Any]:
    t=c.attrib.get("t",""); ref=c.attrib.get("r","")
    f=c.find(f"{{{NS_MAIN}}}f"); v=c.find(f"{{{NS_MAIN}}}v")
    value:Any=""
    if t=="inlineStr":
        value="".join(x.text or "" for x in c.iter() if x.tag.endswith("}t"))
    elif t=="s" and v is not None:
        try:value=strings[int(v.text or "0")]
        except Exception:value=v.text or ""
    elif t=="b" and v is not None:value="是" if (v.text or "0")=="1" else "否"
    elif v is not None:value=v.text or ""
    return {"ref":ref,"value":value,"formula":(f.text or "") if f is not None else ""}


def normalize_formula(formula:str,row_num:int,col_to_key:dict[int,str])->str|None:
    if not formula:return None
    expr=formula.strip()
    if expr.startswith("="):expr=expr[1:]
    # 只自动转换同一行、纯算术/括号/常见聚合；跨表、范围和函数保留为证据但不自动执行。
    unsafe=False
    def repl(m:re.Match[str])->str:
        nonlocal unsafe
        col,row=m.group(1),int(m.group(2))
        if row!=row_num:
            unsafe=True; return m.group(0)
        key=col_to_key.get(excel_col_index(col))
        if not key:
            unsafe=True; return m.group(0)
        return key
    expr=re.sub(r"\$?([A-Z]{1,3})\$?(\d+)",repl,expr.upper())
    expr=expr.replace("^","**")
    if unsafe:return None
    if re.search(r"[^A-Za-z0-9_+\-*/()., <>=]",expr):return None
    # SUM(a,b) / ROUND(a,2) 可由运行时白名单计算器支持；其他函数不自动执行。
    funcs=re.findall(r"\b([A-Z][A-Z0-9_]*)\s*\(",expr)
    if any(f not in {"SUM","ROUND","MIN","MAX","ABS"} for f in funcs):return None
    return expr.lower()


def object_from_matrix(label:str,source_file:str,source_part:str,rows:list[dict[int,dict[str,Any]]],object_key:str)->dict[str,Any]|None:
    if not rows:return None
    header_idx=choose_header_row(rows)
    header=rows[header_idx-1] if header_idx-1<len(rows) else rows[0]
    max_col=max((max(r.keys(),default=0) for r in rows),default=0)
    raw_headers=[header.get(c,{}).get("value","") for c in range(1,max_col+1)]
    headers=normalize_headers(raw_headers)
    # 去掉尾部完全空列
    last=0
    for c,h in enumerate(headers,1):
        if norm_label(raw_headers[c-1]) or any(norm_label(r.get(c,{}).get("value","")) for r in rows[header_idx:]):last=c
    if last<1:return None
    headers=headers[:last]; max_col=last
    data_rows=rows[header_idx:]
    fields=[]; col_to_key={c:f"c{c:02d}" for c in range(1,max_col+1)}
    for c,h in enumerate(headers,1):
        vals=[r.get(c,{}).get("value","") for r in data_rows[:500]]
        non=[norm_label(v) for v in vals if norm_label(v)]
        uniq=len(set(non)); nullable=any(not norm_label(v) for v in vals) if vals else True
        candidate_unique=bool(non) and len(non)>=2 and uniq==len(non)
        samples=[]
        for v in non:
            if v not in samples:samples.append(v)
            if len(samples)>=80:break
        examples=samples[:5]
        distinct_ratio=(uniq/len(non)) if non else 0.0
        enum_candidates=samples[:20] if 1 < uniq <= 12 and distinct_ratio <= 0.35 else []
        fields.append({
            "key":col_to_key[c],"label":h,"source_column":excel_col_name(c),
            "type":infer_field_type(h,vals),"nullable":nullable,
            "candidate_unique":candidate_unique,"sample_nonempty":len(non),"sample_unique":uniq,
            "sample_distinct_ratio":round(distinct_ratio,4),"examples":examples,"relation_samples":samples,
            "enum_candidates":enum_candidates,
            "evidence":{"file":source_file,"part":source_part,"header_row":header_idx,"column":excel_col_name(c)}
        })
    formulas=[]; seen=set()
    for offset,r in enumerate(data_rows[:500],start=header_idx+1):
        for c,cell in r.items():
            if c>max_col or not cell.get("formula"):continue
            target=col_to_key[c]; original=cell["formula"]
            normalized=normalize_formula(original,offset,col_to_key)
            sig=(target,normalized or original)
            if sig in seen:continue
            seen.add(sig)
            formulas.append({"object_key":object_key,"target_field":target,"target_label":headers[c-1],"expression":normalized,"original_formula":original,"auto_executable":bool(normalized),"evidence":{"file":source_file,"part":source_part,"cell":cell.get("ref")}})
    unique_candidates=[]
    for f in fields:
        lab=f["label"].lower()
        if f["candidate_unique"] and any(k in lab for k in ("编号","编码","单号","工号","id","code","序号")):
            unique_candidates.append([f["key"]])
    if not unique_candidates:
        for f in fields:
            if f["candidate_unique"]: unique_candidates.append([f["key"]])
            if len(unique_candidates)>=3:break
    density=sum(1 for r in data_rows[:100] for c in range(1,max_col+1) if norm_label(r.get(c,{}).get("value","")))
    denom=max(1,min(len(data_rows),100)*max_col)
    confidence=min(99,int(50+30*(density/denom)+min(19,len(fields)))) if fields else 20
    return {
        "key":object_key,"label":label or object_key,"source":{"file":source_file,"part":source_part,"kind":"table"},
        "header_row":header_idx,"sampled_rows":len(data_rows[:500]),"field_count":len(fields),"fields":fields,
        "unique_key_candidates":unique_candidates,"calculation_rules":formulas,"confidence_score":confidence
    }


def extract_xlsx(path:Path,next_id:int)->tuple[list[dict],list[str],int]:
    objects=[]; notes=[]
    try:
        with zipfile.ZipFile(path) as z:
            strings=shared_strings(z)
            for sheet_name,target in workbook_sheet_targets(z):
                if not target or target not in z.namelist():
                    notes.append(f"{path.name}:{sheet_name} 无法定位工作表 XML") ; continue
                try:root=ET.fromstring(z.read(target))
                except ET.ParseError:
                    notes.append(f"{path.name}:{sheet_name} 工作表 XML 损坏") ; continue
                rows=[]
                for row in root.findall(f".//{{{NS_MAIN}}}sheetData/{{{NS_MAIN}}}row")[:600]:
                    rd={}
                    for c in row.findall(f"{{{NS_MAIN}}}c")[:200]:
                        cell=parse_xlsx_cell(c,strings); idx=excel_col_index(cell["ref"])
                        if idx:rd[idx]=cell
                    rows.append(rd)
                obj=object_from_matrix(sheet_name,path.name,sheet_name,rows,f"obj_{next_id:03d}")
                if obj and obj["field_count"]:
                    objects.append(obj); next_id+=1
    except (OSError,zipfile.BadZipFile,KeyError,ET.ParseError) as e:
        notes.append(f"{path.name} 解析失败：{e}")
    return objects,notes,next_id


def extract_delimited(path:Path,next_id:int)->tuple[list[dict],list[str],int]:
    notes=[]
    try:
        raw=path.read_bytes()[:2_000_000]; text=decode(raw)
        dialect=csv.excel_tab if path.suffix.lower()==".tsv" else csv.Sniffer().sniff(text[:32768],delimiters=",;\t|")
    except Exception:
        dialect=csv.excel_tab if path.suffix.lower()==".tsv" else csv.excel
        try:text=decode(path.read_bytes()[:2_000_000])
        except Exception as e:return [],[f"{path.name} 读取失败：{e}"],next_id
    try:
        rr=list(csv.reader(text.splitlines(),dialect))[:501]
    except csv.Error as e:return [],[f"{path.name} CSV 解析失败：{e}"],next_id
    rows=[]
    for rno,row in enumerate(rr,1):
        rd={}
        for c,v in enumerate(row,1):rd[c]={"ref":f"{excel_col_name(c)}{rno}","value":v,"formula":""}
        rows.append(rd)
    obj=object_from_matrix(path.stem,path.name,"table",rows,f"obj_{next_id:03d}")
    return ([obj] if obj else []),notes,next_id+(1 if obj else 0)


def extract_json(path:Path,next_id:int)->tuple[list[dict],list[str],int]:
    try:data=json.loads(decode(path.read_bytes()[:20_000_000]))
    except Exception as e:return [],[f"{path.name} JSON 解析失败：{e}"],next_id
    rows=[]
    if isinstance(data,list) and data and all(isinstance(x,dict) for x in data[:500]):
        keys=[]
        for x in data[:500]:
            for k in x:
                if str(k) not in keys:keys.append(str(k))
        rows.append({i+1:{"ref":f"{excel_col_name(i+1)}1","value":k,"formula":""} for i,k in enumerate(keys)})
        for ridx,x in enumerate(data[:500],2):
            rows.append({i+1:{"ref":f"{excel_col_name(i+1)}{ridx}","value":x.get(k,""),"formula":""} for i,k in enumerate(keys)})
    elif isinstance(data,dict):
        rows=[{1:{"ref":"A1","value":"字段","formula":""},2:{"ref":"B1","value":"值","formula":""}}]
        for ridx,(k,v) in enumerate(list(data.items())[:500],2):
            rows.append({1:{"ref":f"A{ridx}","value":k,"formula":""},2:{"ref":f"B{ridx}","value":json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v,"formula":""}})
    obj=object_from_matrix(path.stem,path.name,"json",rows,f"obj_{next_id:03d}") if rows else None
    return ([obj] if obj else []),[],next_id+(1 if obj else 0)


def docx_text_and_tables(path:Path,next_id:int)->tuple[list[dict],list[dict],list[str],int]:
    objects=[]; evidence=[]; notes=[]
    try:
        with zipfile.ZipFile(path) as z:
            root=ET.fromstring(z.read("word/document.xml")); ns={"w":"http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
            paras=[]
            for p in root.findall(".//w:p",ns):
                t="".join(x.text or "" for x in p.findall(".//w:t",ns)).strip()
                if t:paras.append(t)
            if paras:evidence.append({"file":path.name,"kind":"document_text","text":"\n".join(paras[:200])[:30000]})
            for ti,tbl in enumerate(root.findall(".//w:tbl",ns),1):
                rows=[]
                for ri,tr in enumerate(tbl.findall("./w:tr",ns)[:501],1):
                    rd={}
                    for ci,tc in enumerate(tr.findall("./w:tc",ns)[:100],1):
                        txt="".join(x.text or "" for x in tc.findall(".//w:t",ns)).strip()
                        rd[ci]={"ref":f"R{ri}C{ci}","value":txt,"formula":""}
                    rows.append(rd)
                obj=object_from_matrix(f"{path.stem}-表{ti}",path.name,f"table:{ti}",rows,f"obj_{next_id:03d}")
                if obj and obj["field_count"]:objects.append(obj); next_id+=1
    except Exception as e:notes.append(f"{path.name} Word 解析失败：{e}")
    return objects,evidence,notes,next_id


def extract_pdf_text(path:Path)->tuple[list[dict],list[str]]:
    # 优先使用可用的 pypdf；不可用时明确降级，不把乱码当业务事实。
    try:
        from pypdf import PdfReader  # type: ignore
        reader=PdfReader(str(path)); texts=[]
        for page in reader.pages[:80]:
            try:texts.append(page.extract_text() or "")
            except Exception:pass
        text="\n".join(texts).strip()
        return ([{"file":path.name,"kind":"pdf_text","text":text[:50000]}] if text else []),([] if text else [f"{path.name} 未提取到可用 PDF 文本"])
    except Exception:
        return [],[f"{path.name} 未安装/不可用 pypdf，PDF 仅作为文件证据，不自动推断正文规则"]


def _identity_semantic(label:str)->str:
    s=re.sub(r"[\s_\-（）()]+","",str(label or "").lower())
    aliases={
        "员工编号":"person_id","员工工号":"person_id","工号":"person_id","人员编号":"person_id","人员编码":"person_id",
        "设备编号":"equipment_id","设备编码":"equipment_id","资产编号":"equipment_id","资产编码":"equipment_id",
        "物料编号":"material_id","物料编码":"material_id","产品编号":"product_id","产品编码":"product_id",
        "订单编号":"order_id","订单号":"order_id","单号":"document_id",
    }
    if s in aliases:return aliases[s]
    if re.search(r"(?:编号|编码|工号|单号|id|code)$",s):
        stem=re.sub(r"(?:编号|编码|工号|单号|id|code)$","",s)
        return (stem or "generic")+"_id"
    if re.search(r"(?:名称|姓名|name)$",s):
        stem=re.sub(r"(?:名称|姓名|name)$","",s)
        return (stem or "generic")+"_name"
    return s


def _sample_overlap(a:dict,b:dict)->tuple[int,float]:
    sa={norm_label(x).lower() for x in a.get("relation_samples",[]) if norm_label(x)}
    sb={norm_label(x).lower() for x in b.get("relation_samples",[]) if norm_label(x)}
    if not sa or not sb:return 0,0.0
    common=len(sa&sb)
    return common,(common/min(len(sa),len(sb))) if min(len(sa),len(sb)) else 0.0


def detect_relationships(objects:list[dict])->list[dict]:
    """基于字段语义、样本值重合和唯一性推断候选关系。

    仅输出候选关系，不自动升级为数据库外键。不同字段名但值域高度重合时也能识别。
    """
    rels=[]; seen=set()
    for i,a in enumerate(objects):
        for b in objects[i+1:]:
            for fa in a.get("fields",[]):
                la=fa.get("label","").strip().lower(); sema=_identity_semantic(la)
                if not la or len(la)<2:continue
                for fb in b.get("fields",[]):
                    lb=fb.get("label","").strip().lower(); semb=_identity_semantic(lb)
                    if not lb or len(lb)<2:continue
                    type_ok=fa.get("type")==fb.get("type") or {fa.get("type"),fb.get("type")} <= {"integer","number","text"}
                    if not type_ok:continue
                    common,overlap=_sample_overlap(fa,fb)
                    exact=(la==lb)
                    semantic=(sema==semb and (sema.endswith("_id") or sema.endswith("_name")))
                    a_unique=bool(fa.get("candidate_unique")); b_unique=bool(fb.get("candidate_unique"))
                    value_evidence=common>=2 and overlap>=0.35
                    # 字段名不同且无语义对应时，只有“值域高重合 + 至少一侧候选唯一”才认为可能是引用关系。
                    if not (exact or semantic or (value_evidence and (a_unique or b_unique))):continue
                    if exact and value_evidence:score=92
                    elif semantic and value_evidence:score=90
                    elif value_evidence and overlap>=0.75:score=88
                    elif exact:score=76 if (fa.get("candidate_unique") or fb.get("candidate_unique")) else 62
                    elif semantic:score=72 if (fa.get("candidate_unique") or fb.get("candidate_unique")) else 60
                    else:score=min(84,65+int(overlap*20))
                    kind="candidate_reference"; parent=None; child=None
                    if a_unique != b_unique:
                        kind="candidate_one_to_many"
                        parent=a["key"] if a_unique else b["key"]; child=b["key"] if a_unique else a["key"]
                        score=min(96,score+4)
                    reason=[]
                    if exact:reason.append(f"同名字段：{fa.get('label')}")
                    elif semantic:reason.append(f"语义同类字段：{fa.get('label')} ↔ {fb.get('label')}")
                    if value_evidence:reason.append(f"样本值重合 {common} 个，覆盖较小值域 {overlap:.0%}")
                    if a_unique or b_unique:reason.append("一侧样本具候选唯一性")
                    sig=(a["key"],fa["key"],b["key"],fb["key"]);
                    if sig in seen:continue
                    seen.add(sig)
                    rel={"from_object":a["key"],"from_field":fa["key"],"to_object":b["key"],"to_field":fb["key"],"kind":kind,"confidence_score":score,"reason":"；".join(reason) or "样本值域重合"}
                    if parent:rel.update({"candidate_parent_object":parent,"candidate_child_object":child,"sample_overlap_ratio":round(overlap,4),"sample_overlap_count":common})
                    rels.append(rel)
    rels.sort(key=lambda x:x.get("confidence_score",0),reverse=True)
    return rels[:100]

def build_model(source:Path)->dict:
    files=[source] if source.is_file() else [p for p in sorted(source.rglob("*")) if p.is_file() and not p.is_symlink() and "__MACOSX" not in p.parts and not p.name.startswith("~$")]
    objects=[]; evidence=[]; notes=[]; next_id=1
    for p in files:
        suf=p.suffix.lower()
        if suf in {".xlsx",".xlsm"}:
            got,n,next_id=extract_xlsx(p,next_id); objects+=got; notes+=n
        elif suf in {".csv",".tsv"}:
            got,n,next_id=extract_delimited(p,next_id); objects+=got; notes+=n
        elif suf==".json":
            got,n,next_id=extract_json(p,next_id); objects+=got; notes+=n
        elif suf==".docx":
            got,ev,n,next_id=docx_text_and_tables(p,next_id); objects+=got; evidence+=ev; notes+=n
        elif suf==".pdf":
            ev,n=extract_pdf_text(p); evidence+=ev; notes+=n
        elif suf in {".txt",".md"}:
            try:evidence.append({"file":p.name,"kind":"text","text":decode(p.read_bytes()[:500000])})
            except Exception as e:notes.append(f"{p.name} 文本读取失败：{e}")
    relationships=detect_relationships(objects)
    # 值域样本只用于当前进程的关系推断，不写入业务模型产物，减少业务数据暴露。
    for o in objects:
        for f in o.get("fields",[]): f.pop("relation_samples",None)
    rules=[r for o in objects for r in o.get("calculation_rules",[])]
    fields=sum(len(o.get("fields",[])) for o in objects)
    structured=sum(1 for o in objects if o.get("field_count",0)>0)
    auto_rules=sum(1 for r in rules if r.get("auto_executable"))
    if structured:
        avg=sum(o.get("confidence_score",0) for o in objects)/structured
        confidence=min(99,int(avg + min(10,structured*2)))
    else:confidence=0
    open_questions=[]
    if not objects:open_questions.append("未从结构化材料中提取到可生成的业务对象/字段；需要补充 Excel/CSV/JSON 或可解析表格。")
    for o in objects:
        if not o.get("unique_key_candidates"):
            open_questions.append(f"{o['label']}：未发现可靠的业务唯一键；系统可先使用内部记录ID，但导入防重口径待确认。")
    if rules and auto_rules<len(rules):open_questions.append("存在无法安全转换为服务器端表达式的 Excel 公式；这些公式会保留证据但不会自动执行，需确认后再实现。")
    return {
        "schema_version":"2.1","generated_at":datetime.now(timezone.utc).isoformat(),"source":str(source.resolve()),"read_only":True,
        "summary":{"files_scanned":len(files),"structured_objects":len(objects),"fields":fields,"calculation_rules":len(rules),"auto_executable_rules":auto_rules,"candidate_relationships":len(relationships),"model_confidence_score":confidence},
        "business_objects":objects,"calculation_rules":rules,"relationships":relationships,"text_evidence":evidence,"notes":notes,"open_questions":open_questions,
        "policy":"字段、公式、关系均保留来源证据；候选唯一键和候选关系只有在附件事实足够明确或用户确认后，才可升级为正式业务约束。"
    }


def render(model:dict)->str:
    s=model["summary"]
    lines=["# BUSINESS_MODEL_REPORT","",f"- 结构化业务对象：**{s['structured_objects']}**",f"- 字段：**{s['fields']}**",f"- 公式证据：**{s['calculation_rules']}**（可安全自动执行 {s['auto_executable_rules']}）",f"- 候选跨表关系：**{s['candidate_relationships']}**",f"- 模型置信度：**{s['model_confidence_score']}%**","","## 业务对象",""]
    for o in model.get("business_objects",[]):
        lines += [f"### {o['label']} (`{o['key']}`)",f"来源：`{o['source']['file']}` / `{o['source']['part']}`；表头行：{o['header_row']}；抽样数据行：{o['sampled_rows']}","","| 字段 | 类型 | 可空 | 候选唯一 | 来源列 |","|---|---|---|---|---|"]
        for f in o.get("fields",[]):lines.append(f"| {f['label']} (`{f['key']}`) | {f['type']} | {'是' if f['nullable'] else '否'} | {'是' if f['candidate_unique'] else '否'} | {f.get('source_column','')} |")
        if o.get("calculation_rules"):
            lines += ["","公式证据："]
            for r in o["calculation_rules"]:lines.append(f"- {r['target_label']}：`{r['original_formula']}` → {('`'+r['expression']+'`') if r.get('expression') else '仅保留证据，暂不自动执行'}")
        lines.append("")
    lines += ["## 候选关系",""]
    if model.get("relationships"):
        for r in model["relationships"]:lines.append(f"- `{r['from_object']}.{r['from_field']}` ↔ `{r['to_object']}.{r['to_field']}`：{r['reason']}（{r['confidence_score']}%）")
    else:lines.append("- 暂未发现可解释的跨对象关系证据。")
    lines += ["","## 待确认",""]
    if model.get("open_questions"):
        lines += [f"- {q}" for q in model["open_questions"]]
    else:lines.append("- 未发现结构级阻断；业务权限、审批和正式统计口径仍需按资料核对。")
    if model.get("notes"):
        lines += ["","## 解析降级/提示",""]+[f"- {n}" for n in model["notes"]]
    lines += ["","> 本报告把可生成结构与待确认业务规则分开；候选关系/唯一键不等于已确认正式规则。",""]
    return "\n".join(lines)


def main()->int:
    ap=argparse.ArgumentParser(description="深度提取业务对象、字段、公式与跨表关系。")
    ap.add_argument("source"); ap.add_argument("--output",default="business-model.json"); ap.add_argument("--report",default=None)
    a=ap.parse_args(); src=Path(a.source).expanduser()
    if not src.exists():print("[PB001] 输入路径不存在");return 1
    model=build_model(src); Path(a.output).write_text(json.dumps(model,ensure_ascii=False,indent=2),encoding="utf-8")
    if a.report:Path(a.report).write_text(render(model),encoding="utf-8")
    s=model["summary"]
    print(f"[完成] 提取业务对象 {s['structured_objects']} 个、字段 {s['fields']} 个、公式 {s['calculation_rules']} 条，模型置信度 {s['model_confidence_score']}%")
    return 0

if __name__=="__main__":raise SystemExit(main())
