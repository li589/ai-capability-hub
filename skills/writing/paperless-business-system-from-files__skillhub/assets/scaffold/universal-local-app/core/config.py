from __future__ import annotations
import os, sys
from pathlib import Path

APP_ID='paperless-local-{{SYSTEM_NAME}}'
SYSTEM_NAME='{{SYSTEM_NAME}}'

def app_root() -> Path:
    if getattr(sys,'frozen',False): return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]
ROOT=app_root()
DATA_DIR=Path(os.environ.get('DATA_DIR') or ROOT/'data').resolve()
DATA_DIR.mkdir(parents=True,exist_ok=True)
DB_PATH=DATA_DIR/'app.db'
RUNTIME_DIR=DATA_DIR/'runtime'; RUNTIME_DIR.mkdir(parents=True,exist_ok=True)
BACKUP_DIR=DATA_DIR/'backups'; BACKUP_DIR.mkdir(parents=True,exist_ok=True)
SECRET_FILE=DATA_DIR/'flask_secret.txt'
CREDENTIAL_FILE=DATA_DIR/'首次管理员凭据.txt'
