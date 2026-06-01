from config import CONTACTS_FILE
from infrastructure.persistence.json_repository import JsonRepository


class ContactRepository(JsonRepository):

    def __init__(self):
        super().__init__(
            CONTACTS_FILE,
            "contact_id"
        )