from infrastructure.persistence.json_repository import JsonRepository
from config import ROSTER_FILE

class AgentRepository(JsonRepository):
    def __init__(self):
        super().__init__(ROSTER_FILE, key_field='agent_id')