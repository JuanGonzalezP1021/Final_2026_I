import json
import os
from datetime import datetime
from config import AUDIT_LOG_FILE

def audit_log(operation: str, entity: str, payload: dict) -> None:
    """Append-only JSONL audit log."""
    os.makedirs(os.path.dirname(AUDIT_LOG_FILE), exist_ok=True)
    
    entry = {
        'ts': datetime.now().isoformat(),
        'operation': operation,
        'entity': entity,
        'payload': payload,
    }
    
    with open(AUDIT_LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(json.dumps(entry, default=str) + '\n')