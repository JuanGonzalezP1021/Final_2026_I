from controllers.contact_controller import ContactController


class ContactView:

    def __init__(self):
        self.controller = ContactController()

    def show_contacts(self):
        contacts = self.controller.get_all_contacts()

        for contact in contacts:
            print(contact)

    def delete_contact(self, contact_id):
        self.controller.delete_contact(contact_id)