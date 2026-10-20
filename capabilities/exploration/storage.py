"""Small shared persistence helpers for the single harness state owner."""
import hashlib
import json


def digest(value):
    raw=json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


def save(path,value):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')
    temporary.replace(path)
