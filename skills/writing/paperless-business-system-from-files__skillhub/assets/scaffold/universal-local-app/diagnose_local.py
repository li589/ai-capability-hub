from __future__ import annotations
import importlib.util, json, platform, sqlite3
from core.config import DATA_DIR, DB_PATH, ROOT
from core.lifecycle import load_state

def yesno(v): return '通过' if v else '失败'
def main():
    checks=[]
    checks.append(('Python/OS',platform.python_version()+' / '+platform.platform()))
    for mod in ('flask','waitress','openpyxl'):
        checks.append((f'依赖 {mod}',yesno(importlib.util.find_spec(mod) is not None)))
    writable=False
    try:
        t=DATA_DIR/'._write_test'; t.write_text('ok',encoding='utf-8'); t.unlink(); writable=True
    except Exception: pass
    checks.append(('数据目录可写',yesno(writable)))
    if DB_PATH.exists():
        try:
            c=sqlite3.connect(str(DB_PATH)); integ=c.execute('PRAGMA integrity_check').fetchone()[0]; c.close()
            checks.append(('数据库完整性',integ))
        except Exception as e: checks.append(('数据库完整性','失败：'+str(e)))
    else: checks.append(('数据库','首次成功启动后创建'))
    s=load_state(); checks.append(('运行状态',json.dumps({k:s.get(k) for k in ('app_id','pid','port','url')},ensure_ascii=False)))
    report='\n'.join(f'{k}：{v}' for k,v in checks); (ROOT/'data'/'诊断报告.txt').write_text(report,encoding='utf-8'); print(report); return 0
if __name__=='__main__': raise SystemExit(main())
