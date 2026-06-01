from domain.models.contact import Contact
from domain.rules.contact_rules import validate_contact
from infrastructure.persistence.contact_repository import ContactRepository


class ContactController:

    def __init__(self):
        self.repository = ContactRepository()

    def create_contact(self, contact: Contact):
        validate_contact(contact)

        self.repository.insert(
            contact.to_dict()
        )

    def get_all_contacts(self):
        records = self.repository.find_all()

        return [
            Contact.from_dict(r)
            for r in records
        ]

    def delete_contact(self, contact_id):
        self.repository.delete(contact_id)