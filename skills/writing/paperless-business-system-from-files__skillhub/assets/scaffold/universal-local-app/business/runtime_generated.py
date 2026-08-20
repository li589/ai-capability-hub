from __future__ import annotations

import ast
import csv
import io
import json
import re
import secrets
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable
from flask import Blueprint, abort, redirect, render_template, request, send_file, url_for

from core.audit import audit
from core.db import connect, one, query
from core.excel_io import require_openpyxl
from core.rbac import current_permissions, current_user, login_required

ROOT=Path(__file__).resolve().parents[1]
SCHEMA_PATH=Path(__file__).with_name('generated_schema.json')
STAGING_DIR=ROOT/'data'/'import_staging'
bp=Blueprint('business',__name__,url_prefix='/business')


def load_schema()->dict:
    if not SCHEMA_PATH.is_file(): return {'objects':[]}
    try:return json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    except Exception:return {'objects':[]}


def get_object(key:str)->dict:
    for o in load_schema().get('objects',[]):
        if o.get('key')==key:return o
    abort(404)


def permission(code:str):
    u=current_user()
    if not u:return False
    return code in current_permissions()


def require_permission(code:str):
    if not current_user(): abort(401)
    if code not in current_permissions(): abort(403)


def ensure_business_permissions():
    schema=load_schema(); objects=schema.get('objects',[])
    if not objects:return
    with connect() as c:
        role=c.execute("SELECT id FROM roles WHERE name='管理员'").fetchone()
        if not role:return
        for o in objects:
            for action,label in [('view','查看'),('create','新增'),('edit','修改'),('delete','删除'),('import','导入'),('export','导出')]:
                code=f"biz.{o['key']}.{action}"; name=f"{label}{o.get('label',o['key'])}"
                c.execute('INSERT OR IGNORE INTO permissions(code,name) VALUES(?,?)',(code,name))
                c.execute('INSERT OR IGNORE INTO role_permissions(role_id,permission_code) VALUES(?,?)',(role['id'],code))


class SafeCalc:
    FUNCS={'sum':lambda *x:sum(x),'round':round,'min':min,'max':max,'abs':abs}
    def __init__(self,values:dict[str,Any]):self.values=values
    def eval(self,expr:str):return self.visit(ast.parse(expr,mode='eval').body)
    def visit(self,n):
        if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)):return n.value
        if isinstance(n,ast.Name):return self._num(self.values.get(n.id))
        if isinstance(n,ast.BinOp):
            a,b=self.visit(n.left),self.visit(n.right)
            ops={ast.Add:lambda:a+b,ast.Sub:lambda:a-b,ast.Mult:lambda:a*b,ast.Div:lambda:a/b if b!=0 else None,ast.Pow:lambda:a**b,ast.Mod:lambda:a%b if b!=0 else None}
            fn=ops.get(type(n.op))
            if not fn:raise ValueError('unsupported operator')
            return fn()
        if isinstance(n,ast.UnaryOp):
            v=self.visit(n.operand)
            if isinstance(n.op,ast.USub):return -v
            if isinstance(n.op,ast.UAdd):return v
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in self.FUNCS:
            return self.FUNCS[n.func.id](*[self.visit(x) for x in n.args])
        raise ValueError('unsupported expression')
    @staticmethod
    def _num(v):
        if v in (None,''):return 0
        try:return int(v) if re.fullmatch(r'[-+]?\d+',str(v).strip()) else float(v)
        except Exception:raise ValueError('calculation input is not numeric')


def apply_calculations(obj:dict,payload:dict)->tuple[dict,list[str]]:
    out=dict(payload); errors=[]
    for r in obj.get('calculations',[]):
        expr=r.get('expression')
        if not expr:continue
        try:
            val=SafeCalc(out).eval(expr)
            out[r['target_field']]='' if val is None else val
        except Exception as e:
            errors.append(f"计算字段 {r.get('target_field')} 失败：{e}")
    return out,errors


def _parse_date(s:str)->str:
    for fmt in ('%Y-%m-%d','%Y/%m/%d','%Y.%m.%d'):
        try:return datetime.strptime(s,fmt).date().isoformat()
        except ValueError:pass
    try:return date.fromisoformat(s).isoformat()
    except Exception:raise ValueError('必须为有效日期，例如 2026-08-18')


def _parse_datetime(s:str)->str:
    text=s.replace('T',' ')
    for fmt in ('%Y-%m-%d %H:%M','%Y-%m-%d %H:%M:%S','%Y/%m/%d %H:%M'):
        try:return datetime.strptime(text,fmt).isoformat(sep=' ',timespec='seconds')
        except ValueError:pass
    try:return datetime.fromisoformat(text).isoformat(sep=' ',timespec='seconds')
    except Exception:raise ValueError('必须为有效日期时间，例如 2026-08-18 09:30')


def coerce(field:dict,value:Any):
    if value is None:return None
    s=str(value).strip()
    if s=='':return None
    t=str(field.get('type','text')).lower()
    enums=[str(x) for x in (field.get('enum_candidates') or [])]
    if enums and s not in enums:raise ValueError('必须选择允许的值：'+' / '.join(enums[:12]))
    if t=='integer':
        if not re.fullmatch(r'[-+]?\d+',s):raise ValueError('必须为整数')
        return int(s)
    if t=='number':
        try:return float(s)
        except ValueError:raise ValueError('必须为数字')
    if t=='boolean':
        low=s.lower()
        if low in {'1','true','是','yes','y','on'}:return 1
        if low in {'0','false','否','no','n','off'}:return 0
        raise ValueError('必须为“是/否”或 true/false')
    if t=='date':return _parse_date(s)
    if t=='datetime':return _parse_datetime(s)
    return s


def build_payload(obj:dict,getter:Callable[[dict],Any])->tuple[dict,list[str]]:
    values={}; errors=[]
    for f in obj.get('fields',[]):
        if f.get('computed'):continue
        raw=getter(f)
        try:values[f['key']]=coerce(f,raw)
        except ValueError as e:
            values[f['key']]=raw
            errors.append(f"{f['label']}：{e}")
    if errors:return values,errors
    values,calc_errors=apply_calculations(obj,values); errors.extend(calc_errors)
    errors.extend(validate_payload(obj,values))
    return values,errors


def validate_payload(obj:dict,payload:dict)->list[str]:
    errors=[]
    for f in obj.get('fields',[]):
        value=payload.get(f['key'])
        if f.get('required') and value in (None,''):errors.append(f"{f['label']} 不能为空")
        enums=[str(x) for x in (f.get('enum_candidates') or [])]
        if value not in (None,'') and enums and str(value) not in enums:errors.append(f"{f['label']} 不在允许值范围")
    return errors


def row_to_dict(row,obj):
    return {'id':row['id'],**{f['key']:row[f['column']] for f in obj.get('fields',[])},'created_at':row['created_at'],'updated_at':row['updated_at']}


@bp.get('/')
@login_required
def index():
    objects=[]
    for o in load_schema().get('objects',[]):
        if permission(f"biz.{o['key']}.view"):objects.append(o)
    return render_template('business_index.html',objects=objects)


@bp.get('/<key>')
@login_required
def list_records(key):
    obj=get_object(key); require_permission(f'biz.{key}.view')
    q=request.args.get('q','').strip(); page=max(1,int(request.args.get('page','1') or 1)); page_size=30
    fields=obj.get('fields',[]); where=''; params=[]
    if q and fields:
        clauses=[f"CAST({f['column']} AS TEXT) LIKE ?" for f in fields]; where=' WHERE '+' OR '.join(clauses); params=['%'+q+'%']*len(fields)
    total=one(f"SELECT COUNT(*) n FROM {obj['table']}"+where,tuple(params))['n']
    rows=query(f"SELECT * FROM {obj['table']}"+where+' ORDER BY id DESC LIMIT ? OFFSET ?',tuple(params+[page_size,(page-1)*page_size]))
    return render_template('business_list.html',obj=obj,rows=[row_to_dict(r,obj) for r in rows],q=q,page=page,total=total,page_size=page_size,can_create=permission(f'biz.{key}.create'),can_edit=permission(f'biz.{key}.edit'),can_delete=permission(f'biz.{key}.delete'),can_import=permission(f'biz.{key}.import'),can_export=permission(f'biz.{key}.export'))


@bp.route('/<key>/new',methods=['GET','POST'])
@login_required
def new_record(key):
    obj=get_object(key); require_permission(f'biz.{key}.create'); errors=[]; values={}
    if request.method=='POST':
        values,errors=build_payload(obj,lambda f:request.form.get(f['key']))
        if not errors:
            fields=obj.get('fields',[]); cols=[f['column'] for f in fields]; vals=[values.get(f['key']) for f in fields]
            with connect() as c:c.execute(f"INSERT INTO {obj['table']} ({','.join(cols)},created_by,updated_by) VALUES ({','.join('?' for _ in cols)},?,?)",tuple(vals+[current_user()['id'],current_user()['id']]))
            audit(current_user()['id'],f'新增{obj["label"]}',json.dumps(values,ensure_ascii=False)[:3500]); return redirect(url_for('business.list_records',key=key))
    return render_template('business_form.html',obj=obj,values=values,errors=errors,mode='new')


@bp.route('/<key>/<int:rid>/edit',methods=['GET','POST'])
@login_required
def edit_record(key,rid):
    obj=get_object(key); require_permission(f'biz.{key}.edit'); row=one(f"SELECT * FROM {obj['table']} WHERE id=?",(rid,))
    if not row:abort(404)
    values=row_to_dict(row,obj); errors=[]
    if request.method=='POST':
        values,errors=build_payload(obj,lambda f:request.form.get(f['key']))
        if not errors:
            fields=obj.get('fields',[]); sets=','.join(f"{f['column']}=?" for f in fields); vals=[values.get(f['key']) for f in fields]
            with connect() as c:c.execute(f"UPDATE {obj['table']} SET {sets},updated_by=?,updated_at=CURRENT_TIMESTAMP WHERE id=?",tuple(vals+[current_user()['id'],rid]))
            audit(current_user()['id'],f'修改{obj["label"]}',f'id={rid}'); return redirect(url_for('business.list_records',key=key))
    return render_template('business_form.html',obj=obj,values=values,errors=errors,mode='edit')


@bp.post('/<key>/<int:rid>/delete')
@login_required
def delete_record(key,rid):
    obj=get_object(key); require_permission(f'biz.{key}.delete')
    with connect() as c:c.execute(f"DELETE FROM {obj['table']} WHERE id=?",(rid,))
    audit(current_user()['id'],f'删除{obj["label"]}',f'id={rid}'); return redirect(url_for('business.list_records',key=key))


def parse_upload(file_storage,obj):
    name=(file_storage.filename or '').lower(); raw=file_storage.read(12*1024*1024+1)
    if len(raw)>12*1024*1024:raise ValueError('导入文件超过 12 MiB')
    labels=[f['label'] for f in obj.get('fields',[]) if not f.get('computed')]; rows=[]; invalid=[]
    if name.endswith('.xlsx'):
        op=require_openpyxl(); wb=op.load_workbook(io.BytesIO(raw),read_only=True,data_only=False); ws=wb.active
        data=list(ws.iter_rows(values_only=True))
    elif name.endswith('.csv'):
        text=raw.decode('utf-8-sig','ignore'); data=list(csv.reader(io.StringIO(text)))
    else:raise ValueError('仅支持 XLSX 或 CSV')
    if not data:return [],[]
    headers=[str(x or '').strip() for x in data[0]]; index={h:i for i,h in enumerate(headers)}
    missing=[x for x in labels if x not in index]
    if missing:raise ValueError('缺少字段：'+'、'.join(missing[:10]))
    for row_no,row in enumerate(data[1:20001],start=2):
        if not any(x not in (None,'') for x in row):continue
        values,errors=build_payload(obj,lambda f,row=row:row[index[f['label']]] if index[f['label']]<len(row) else None)
        if errors:invalid.append({'row':row_no,'errors':errors,'values':values})
        else:rows.append({'row':row_no,'values':values})
    return rows,invalid


@bp.route('/<key>/import',methods=['GET','POST'])
@login_required
def import_records(key):
    obj=get_object(key); require_permission(f'biz.{key}.import'); error=None; preview=None; token=None; invalid_preview=None; summary=None
    STAGING_DIR.mkdir(parents=True,exist_ok=True)
    if request.method=='POST' and request.form.get('action')=='preview':
        try:
            valid,invalid=parse_upload(request.files['file'],obj); token=secrets.token_urlsafe(18)
            stage={'uid':current_user()['id'],'object':key,'valid_rows':valid,'invalid_rows':invalid}; (STAGING_DIR/(token+'.json')).write_text(json.dumps(stage,ensure_ascii=False),encoding='utf-8')
            preview=[x['values'] for x in valid[:20]]; invalid_preview=invalid[:20]; summary={'valid':len(valid),'invalid':len(invalid),'total':len(valid)+len(invalid)}
        except Exception as e:error=str(e)
    elif request.method=='POST' and request.form.get('action')=='commit':
        token=request.form.get('token',''); p=STAGING_DIR/(token+'.json')
        try:
            stage=json.loads(p.read_text(encoding='utf-8'))
            if stage.get('uid')!=current_user()['id'] or stage.get('object')!=key:abort(403)
            invalid=stage.get('invalid_rows',[])
            if invalid:raise ValueError(f'仍有 {len(invalid)} 行校验失败，已阻止写入；请修正文件后重新预览。')
            rows=[x.get('values',{}) for x in stage.get('valid_rows',[])]; fields=obj.get('fields',[]); cols=[f['column'] for f in fields]
            with connect() as c:
                for values in rows:
                    vals=[values.get(f['key']) for f in fields]
                    c.execute(f"INSERT INTO {obj['table']} ({','.join(cols)},created_by,updated_by) VALUES ({','.join('?' for _ in cols)},?,?)",tuple(vals+[current_user()['id'],current_user()['id']]))
            p.unlink(missing_ok=True); audit(current_user()['id'],f'导入{obj["label"]}',f'{len(rows)} 条'); return redirect(url_for('business.list_records',key=key))
        except Exception as e:error=str(e)
    return render_template('business_import.html',obj=obj,error=error,preview=preview,invalid_preview=invalid_preview,summary=summary,token=token)


@bp.get('/<key>/export.xlsx')
@login_required
def export_records(key):
    obj=get_object(key); require_permission(f'biz.{key}.export'); op=require_openpyxl(); wb=op.Workbook(); ws=wb.active; ws.title=obj.get('label','数据')[:31]
    fields=obj.get('fields',[]); ws.append([f['label'] for f in fields])
    for r in query(f"SELECT * FROM {obj['table']} ORDER BY id"):
        ws.append([r[f['column']] for f in fields])
    bio=io.BytesIO(); wb.save(bio); bio.seek(0); audit(current_user()['id'],f'导出{obj["label"]}')
    return send_file(bio,as_attachment=True,download_name=f"{obj['label']}.xlsx",mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
