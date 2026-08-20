#!/usr/bin/env python3
"""只读盘点业务材料；每个文件必须显式出现在报告中，禁止无声跳过。"""
from __future__ import annotations

import argparse, csv, hashlib, json, os, re, sys, zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable
import xml.etree.ElementTree as ET

SUPPORTED={'.xlsx','.xlsm','.zip','.xls','.csv','.tsv','.docx','.doc','.pdf','.json','.txt','.md'}
DEEP_PROFILED={'.csv','.tsv','.json','.zip','.xlsx','.xlsm','.docx','.pdf'}
ENCODINGS=('utf-8-sig','utf-8','gb18030')
HASH_CHUNK=1024*1024

class ParseFailure(Exception):
    def __init__(self, code:str, stage:str, location:str, cause:str, action:str, impact:str='当前文件无法可靠用于业务建模', resume_point:str='文件解析'):
        super().__init__(cause); self.code=code; self.stage=stage; self.location=location; self.cause=cause; self.action=action; self.impact=impact; self.resume_point=resume_point

def issue(code,severity,stage,location,cause,impact,action,resume_point):
    return {'code':code,'severity':severity,'stage':stage,'location':location,'cause':cause,'impact':impact,'action':action,'resume_point':resume_point}

def sha256_file(path:Path)->str:
    d=hashlib.sha256()
    with path.open('rb') as f:
        while True:
            c=f.read(HASH_CHUNK)
            if not c: break
            d.update(c)
    return d.hexdigest()

def iter_source_files(source:Path)->Iterable[Path]:
    if source.is_file():
        yield source; return
    for p in sorted(source.rglob('*')):
        if p.is_symlink() or not p.is_file(): continue
        if p.name.startswith('~$') or '__MACOSX' in p.parts: continue
        yield p

def read_text_sample(path:Path, limit:int=131072):
    raw=path.read_bytes()[:limit]; errors=[]
    for enc in ENCODINGS:
        try: return raw.decode(enc),enc
        except UnicodeDecodeError as e: errors.append(f'{enc}@{e.start}')
    raise ParseFailure('PB003','编码识别','file',f'无法用 UTF-8/UTF-8-BOM/GB18030 解码；失败位置：{", ".join(errors)}','另存为 UTF-8 或 GB18030 后重试','文本内容无法可靠读取','文件解析')

def choose_dialect(sample:str,suffix:str):
    if suffix=='.tsv': return csv.excel_tab
    try: return csv.Sniffer().sniff(sample[:32768], delimiters=',;\t|')
    except csv.Error: return csv.excel

def normalize_headers(row:list[str])->list[str]:
    out=[]; seen=Counter()
    for i,raw in enumerate(row,1):
        base=str(raw).strip() or f'未命名列{i}'; seen[base]+=1
        out.append(base if seen[base]==1 else f'{base}__重复{seen[base]}')
    return out

def profile_delimited(path:Path,max_rows:int):
    sample,enc=read_text_sample(path); dialect=choose_dialect(sample,path.suffix.lower())
    rows=[]; truncated=False
    try:
        with path.open('r',encoding=enc,newline='') as f:
            r=csv.reader(f,dialect)
            try: raw_headers=next(r)
            except StopIteration: return {'encoding':enc,'delimiter':dialect.delimiter,'headers':[],'sampled_rows':0,'empty_file':True}
            headers=normalize_headers(raw_headers); missing=[0]*len(headers); values=[set() for _ in headers]
            for idx,raw in enumerate(r,start=2):
                if len(rows)>=max_rows: truncated=True; break
                row=list(raw[:len(headers)])+['']*max(0,len(headers)-len(raw)); cleaned=tuple(v.strip() for v in row)
                rows.append(cleaned)
                for c,v in enumerate(cleaned):
                    if v=='': missing[c]+=1
                    else: values[c].add(v)
    except csv.Error as e:
        line=getattr(r,'line_num','?') if 'r' in locals() else '?'
        raise ParseFailure('PB003','CSV 解析',f'line:{line}',f'CSV 结构异常：{e}','检查该行引号、分隔符和换行；修复后从文件解析继续','该行及其后的记录无法可靠读取','文件解析')
    dup=len(rows)-len(set(rows)); keys=[]
    for i,h in enumerate(headers):
        if rows and missing[i]==0 and len(values[i])==len(rows): keys.append(h)
    return {'encoding':enc,'delimiter':dialect.delimiter,'headers':headers,'sampled_rows':len(rows),'sample_truncated':truncated,'missing_by_column':dict(zip(headers,missing)),'duplicate_rows_in_sample':dup,'candidate_unique_columns':keys,'empty_file':False}

def profile_json(path:Path,max_rows:int):
    size=path.stat().st_size
    if size>50*1024*1024: raise ParseFailure('PB003','JSON 大小检查','file','JSON 大于 50 MiB','分片或使用流式导入方案','当前轻量画像不会加载超大 JSON','文件解析')
    text,enc=read_text_sample(path,limit=max(size,1))
    try: val=json.loads(text)
    except json.JSONDecodeError as e:
        raise ParseFailure('PB003','JSON 语法',f'line:{e.lineno},col:{e.colno}',e.msg,'修复该行列附近的逗号、引号、括号或转义字符','JSON 无法建立可靠字段结构','文件解析')
    out={'encoding':enc,'root_type':type(val).__name__}
    if isinstance(val,list):
        sample=val[:max_rows]; out.update(total_items=len(val),sampled_items=len(sample),sample_truncated=len(val)>len(sample))
        if sample and all(isinstance(x,dict) for x in sample):
            keys=sorted({str(k) for x in sample for k in x}); out['keys']=keys; out['missing_by_key']={k:sum(1 for x in sample if x.get(k) in (None,'')) for k in keys}
    elif isinstance(val,dict): out['keys']=sorted(str(k) for k in val)
    return out

def safe_zip_infos(path:Path):
    try: z=zipfile.ZipFile(path)
    except zipfile.BadZipFile as e: raise ParseFailure('PB003','ZIP/Office 容器','file',f'ZIP 容器损坏或不是标准 ZIP：{e}','重新下载/另存为标准文件；若是 Office 文件请用 WPS/Office“另存为”','容器成员无法读取','文件解析')
    infos=z.infolist()
    if len(infos)>5000: z.close(); raise ParseFailure('PB003','ZIP 安全检查','file','成员超过 5000 个','拆分压缩包后处理','防止异常压缩包耗尽资源','文件解析')
    total=sum(max(i.file_size,0) for i in infos); compressed=sum(max(i.compress_size,0) for i in infos)
    if total>2*1024**3: z.close(); raise ParseFailure('PB003','ZIP 安全检查','file','解压后总大小超过 2 GiB','拆分压缩包后处理','超出安全画像上限','文件解析')
    ratio=total/max(compressed,1) if total else 0
    if ratio>200 and total>100*1024**2: z.close(); raise ParseFailure('PB003','ZIP 安全检查','file',f'压缩比异常：{ratio:.1f}','确认不是压缩炸弹并拆分材料','拒绝直接解压以避免资源耗尽','文件解析')
    unsafe=[]
    for i in infos:
        pp=PurePosixPath(i.filename.replace('\\','/'))
        if pp.is_absolute() or '..' in pp.parts: unsafe.append(i.filename)
    if unsafe: z.close(); raise ParseFailure('PB003','ZIP 路径安全',f'member:{unsafe[0]}','发现绝对路径或 .. 路径成员','重新打包，移除越界路径成员','直接解压可能覆盖项目外文件','文件解析')
    return z,infos,total,compressed,ratio

def profile_zip(path:Path):
    z,infos,total,compressed,ratio=safe_zip_infos(path)
    try:
        suffixes=Counter(); members=[]; encrypted=[]
        for i in infos:
            if i.flag_bits & 0x1: encrypted.append(i.filename)
            if not i.is_dir():
                suffixes[Path(i.filename).suffix.lower() or '<none>']+=1
                if len(members)<100: members.append(i.filename)
        return {'member_count':len(infos),'file_count':sum(not i.is_dir() for i in infos),'total_uncompressed_bytes':total,'total_compressed_bytes':compressed,'compression_ratio':round(ratio,2),'encrypted_members':encrypted[:20],'extensions':dict(suffixes.most_common()),'member_sample':members}
    finally: z.close()

def parse_xml_member(z:zipfile.ZipFile,name:str,stage:str):
    try: raw=z.read(name)
    except KeyError: raise ParseFailure('PB003',stage,f'member:{name}',f'缺少必需成员 {name}','用 WPS/Office 重新另存为标准 OOXML 文件','Office 文件结构不完整','文件解析')
    try: return ET.fromstring(raw)
    except ET.ParseError as e:
        loc=f'member:{name}' + (f',line:{e.position[0]},col:{e.position[1]}' if getattr(e,'position',None) else '')
        raise ParseFailure('PB003',stage,loc,f'XML 结构损坏：{e}','用 WPS/Office 打开后另存为新文件；若打不开则恢复备份','对应文档结构无法可靠读取','文件解析')

def profile_xlsx(path:Path):
    z,infos,total,compressed,ratio=safe_zip_infos(path)
    try:
        names={i.filename for i in infos}
        for req in ('[Content_Types].xml','xl/workbook.xml'):
            if req not in names: raise ParseFailure('PB003','Excel 容器结构',f'member:{req}',f'缺少 Excel 必需成员 {req}','用 WPS/Excel 另存为 .xlsx/.xlsm','工作簿结构不完整','文件解析')
        root=parse_xml_member(z,'xl/workbook.xml','Excel 工作簿结构')
        ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        sheets=[]
        for s in root.findall('.//m:sheets/m:sheet',ns):
            sheets.append({'name':s.attrib.get('name',''),'state':s.attrib.get('state','visible'),'rid':next((v for k,v in s.attrib.items() if k.endswith('}id')),'')})
        ws=[n for n in names if n.startswith('xl/worksheets/') and n.endswith('.xml')]
        bad=[]
        for n in ws:
            try: ET.fromstring(z.read(n))
            except ET.ParseError as e: bad.append({'member':n,'line':getattr(e,'position',(None,None))[0],'col':getattr(e,'position',(None,None))[1],'error':str(e)})
        if bad:
            b=bad[0]; raise ParseFailure('PB003','Excel 工作表结构',f'member:{b["member"]},line:{b["line"]},col:{b["col"]}',f'工作表 XML 损坏：{b["error"]}','用 WPS/Excel 打开并另存；若提示修复，保存修复后的副本','至少一个工作表无法可靠读取','文件解析')
        return {'container':'OOXML','sheet_count':len(sheets),'sheets':sheets,'worksheet_xml_count':len(ws),'total_uncompressed_bytes':total,'compression_ratio':round(ratio,2),'has_vba':'xl/vbaProject.bin' in names}
    finally: z.close()

def profile_docx(path:Path):
    z,infos,total,compressed,ratio=safe_zip_infos(path)
    try:
        names={i.filename for i in infos}
        if '[Content_Types].xml' not in names or 'word/document.xml' not in names:
            raise ParseFailure('PB003','Word 容器结构','member:word/document.xml','缺少 Word 主文档 XML','用 WPS/Word 另存为 .docx','文档正文无法读取','文件解析')
        root=parse_xml_member(z,'word/document.xml','Word 正文结构')
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        return {'container':'OOXML','paragraph_count':len(root.findall('.//w:p',ns)),'table_count':len(root.findall('.//w:tbl',ns)),'header_parts':len([n for n in names if n.startswith('word/header') and n.endswith('.xml')]),'footer_parts':len([n for n in names if n.startswith('word/footer') and n.endswith('.xml')]),'total_uncompressed_bytes':total,'compression_ratio':round(ratio,2)}
    finally: z.close()

def profile_pdf(path:Path):
    size=path.stat().st_size
    with path.open('rb') as f:
        head=f.read(16); tail_len=min(size,65536); f.seek(max(0,size-tail_len)); tail=f.read(tail_len)
    if not head.startswith(b'%PDF-'): raise ParseFailure('PB003','PDF 文件头','offset:0','缺少 %PDF- 文件头','重新导出为标准 PDF 或确认扩展名是否错误','不能确认该文件是有效 PDF','文件解析')
    warnings=[]
    if b'%%EOF' not in tail: warnings.append('文件尾未发现 %%EOF，可能被截断或由非标准生成器写出')
    raw=path.read_bytes() if size<=50*1024*1024 else head+tail
    page_count=len(re.findall(br'/Type\s*/Page\b',raw))
    return {'pdf_version':head[5:8].decode('ascii','replace'),'size_bytes':size,'approx_page_objects':page_count,'eof_marker_found':b'%%EOF' in tail,'xref_marker_found':b'xref' in tail or b'/Type/XRef' in tail,'warnings':warnings}

def profile_one(path:Path,source_root:Path,max_rows:int):
    rel=path.name if source_root.is_file() else str(path.relative_to(source_root)); suffix=path.suffix.lower()
    item={'path':rel.replace(os.sep,'/'),'extension':suffix,'size_bytes':0,'sha256':'','supported':suffix in SUPPORTED,'deep_profiled':suffix in DEEP_PROFILED,'status':'ok','issues':[]}
    try:
        item['size_bytes']=path.stat().st_size; item['sha256']=sha256_file(path)
    except OSError as e:
        item['status']='error'; item['issues'].append(issue('PB003','error','文件读取','file',str(e),'无法读取文件元数据或内容','检查文件权限、占用和路径后重试','输入清单')); return item
    if suffix not in SUPPORTED:
        item['status']='warning'; item['issues'].append(issue('PB002','warning','格式识别','file',f'扩展名 {suffix or "<none>"} 不在支持清单','不会自动把该文件映射为业务事实','转换为标准 xlsx/csv/docx/pdf/json/txt 或明确排除','输入清单')); return item
    if suffix in {'.xls','.doc'}:
        item['status']='warning'; item['issues'].append(issue('PB003','warning','旧格式兼容','file',f'{suffix} 为旧式二进制格式','当前离线预检不执行旧格式深解析','用 WPS/Office 另存为 .xlsx/.docx；保留原件','文件解析')); return item
    try:
        if suffix in {'.csv','.tsv'}: item['profile']=profile_delimited(path,max_rows)
        elif suffix=='.json': item['profile']=profile_json(path,max_rows)
        elif suffix=='.zip': item['profile']=profile_zip(path)
        elif suffix in {'.xlsx','.xlsm'}: item['profile']=profile_xlsx(path)
        elif suffix=='.docx': item['profile']=profile_docx(path)
        elif suffix=='.pdf':
            item['profile']=profile_pdf(path)
            for w in item['profile'].get('warnings',[]):
                item['status']='warning'; item['issues'].append(issue('PB003','warning','PDF 结构','file',w,'文本/表格提取结果需要额外复核','重新导出标准 PDF；若能正常打开则继续并人工复核关键字段','文件解析'))
        else:
            item['profile']={'text_file':True}; read_text_sample(path)
    except ParseFailure as e:
        item['status']='error'; item['issues'].append(issue(e.code,'error',e.stage,e.location,e.cause,e.impact,e.action,e.resume_point))
    except (OSError,ValueError,zipfile.BadZipFile,ET.ParseError) as e:
        item['status']='error'; item['issues'].append(issue('PB999','error','未分类解析异常','file',repr(e),'当前文件未完成可靠画像','运行 diagnose.py 并提供最小脱敏样例','文件解析'))
    return item

def build_profile(source:Path,max_rows:int):
    files=list(iter_source_files(source)); items=[profile_one(p,source,max_rows) for p in files]
    errors=sum(i['status']=='error' for i in items); warns=sum(i['status']=='warning' for i in items)
    state='passed' if errors==0 else ('partial_with_errors' if errors<len(items) else 'failed')
    return {'schema_version':'1.1','generated_at':datetime.now(timezone.utc).isoformat(),'source':str(source.resolve()),'read_only':True,'network_used':False,'overall_status':state,'summary':{'total_files':len(items),'supported_files':sum(i['supported'] for i in items),'errors':errors,'warnings':warns,'silently_skipped':0,'requires_attention':errors>0 or warns>0},'files':items}

def parse_args():
    p=argparse.ArgumentParser(description='只读盘点业务文件并生成可定位的数据质量画像。')
    p.add_argument('source'); p.add_argument('--output',default='input-profile.json'); p.add_argument('--max-rows',type=int,default=5000); p.add_argument('--strict',action='store_true',help='存在任一文件 error 时返回非 0；默认仍生成部分成功报告并返回 0')
    return p.parse_args()

def main():
    a=parse_args(); source=Path(a.source).expanduser()
    if not source.exists(): print('[PB001] 输入路径不存在\n处理：检查文件或目录路径后重新运行。\n恢复点：输入清单。'); return 1
    if source.is_symlink(): print('[PB003] 输入路径是符号链接，已拒绝跟随。\n处理：选择真实文件或目录。\n恢复点：输入清单。'); return 1
    if a.max_rows<1: print('[PB001] --max-rows 必须大于 0'); return 1
    try:
        report=build_profile(source,a.max_rows); out=Path(a.output).expanduser(); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    except (OSError,ValueError) as e: print(f'[PB003] 生成输入画像失败：{e}\n处理：检查文件可读性与报告目录权限。\n恢复点：输入清单。'); return 1
    s=report['summary']
    if s['total_files']==0: print('[PB001] 输入目录中没有可盘点文件'); return 1
    print(f'[完成] 共盘点 {s["total_files"]} 个文件；错误 {s["errors"]}，警告 {s["warnings"]}，无声跳过 {s["silently_skipped"]}。总体：{report["overall_status"]}')
    for f in report['files']:
        for x in f.get('issues',[]):
            print(f'[{x["code"]}] {f["path"]} | {x["stage"]} | {x["location"]} | {x["cause"]}')
            print(f'  影响：{x["impact"]}\n  处理：{x["action"]}\n  恢复点：{x["resume_point"]}')
    print(f'报告：{out.resolve()}')
    return 1 if a.strict and s['errors'] else 0

if __name__=='__main__': sys.exit(main())
