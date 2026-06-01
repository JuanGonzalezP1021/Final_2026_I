import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ROSTER_FILE = os.path.join(DATA_DIR, "roster.json")
CONTACTS_FILE = os.path.join(DATA_DIR, "contacts.json")
PRODUCTIVITY_FILE = os.path.join(DATA_DIR, "productivity.json")
AUDIT_LOG_FILE = os.path.join(DATA_DIR, "audit.log")
EMAIL_SENDER = "noreply@callcenter.local"
EMAIL_RECIPIENTS = ["ops-supervisor@callcenter.local"]
MAX_AGENTS_PER_TL = 15
MAX_CONTACTS_PER_AGENT_DAY = 200
MISSED_THRESHOLD_PER_DAY = 5
MAX_LOGIN_DURATION_SEC = 43200
MIN_OCCUPANCY = 0.40
MAX_AUX_RATIO = 0.30
