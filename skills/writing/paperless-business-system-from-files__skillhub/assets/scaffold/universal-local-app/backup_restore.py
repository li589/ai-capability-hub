from __future__ import annotations
import argparse, shutil
from pathlib import Path
from core.backup import create_backup, integrity_ok
from core.config import DB_PATH
from core.lifecycle import load_state

def main():
    ap=argparse.ArgumentParser(); sp=ap.add_subparsers(dest='cmd',required=True)
    sp.add_parser('backup'); r=sp.add_parser('restore'); r.add_argument('file')
    a=ap.parse_args()
    if a.cmd=='backup': print(create_backup()); return 0
    state=load_state()
    if state.get('pid'):
        print('恢复前必须先停止本项目服务，避免数据库写入竞争。'); return 1
    src=Path(a.file)
    if not src.is_file() or not integrity_ok(src): print('备份文件完整性校验失败'); return 1
    rollback=create_backup('before_restore'); shutil.copy2(src,DB_PATH); print('恢复完成；回滚副本：',rollback); return 0
if __name__=='__main__': raise SystemExit(main())
