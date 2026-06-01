from __future__ import annotations
from infrastructure.persistence.json_repository import JsonRepository
from config import PRODUCTIVITY_FILE

class ProductivityRepository(JsonRepository):
    def __init__(self):
        super().__init__(PRODUCTIVITY_FILE, key_field='record_id')