from __future__ import annotations
import base64, hashlib, hmac, os, secrets

def hash_password(password:str)->str:
    salt=os.urandom(16); rounds=260000
    dk=hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt,rounds)
    return f'pbkdf2_sha256${rounds}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}'

def verify_password(password:str, stored:str)->bool:
    try:
        alg,rounds,salt_b64,digest_b64=stored.split('$',3)
        if alg!='pbkdf2_sha256': return False
        salt=base64.b64decode(salt_b64); expected=base64.b64decode(digest_b64)
        actual=hashlib.pbkdf2_hmac('sha256',password.encode('utf-8'),salt,int(rounds))
        return hmac.compare_digest(actual,expected)
    except Exception: return False

def random_password()->str: return secrets.token_urlsafe(14)
