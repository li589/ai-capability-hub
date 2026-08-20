from __future__ import annotations
from .db import execute

def audit(user_id,action,detail=''):
    execute('INSERT INTO audit_log(user_id,action,detail) VALUES(?,?,?)',(user_id,action,str(detail)[:4000]))
