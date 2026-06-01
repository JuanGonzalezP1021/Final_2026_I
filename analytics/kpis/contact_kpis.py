class ContactKPI:

    @staticmethod
    def total_contacts(contacts):
        return sum(
            c.inbound_tx +
            c.outbound_tx +
            c.missed_tx
            for c in contacts
        )

    @staticmethod
    def total_handled(contacts):
        return sum(
            c.inbound_tx +
            c.outbound_tx
            for c in contacts
        )

    @staticmethod
    def total_missed(contacts):
        return sum(
            c.missed_tx
            for c in contacts
        )

    @staticmethod
    def average_aht(contacts):
        handled = ContactKPI.total_handled(contacts)

        if handled == 0:
            return 0.0

        total_time = sum(
            c.handle_time_sec +
            c.acw_sec
            for c in contacts
        )

        return total_time / handled

    @staticmethod
    def missed_rate(contacts):
        total = ContactKPI.total_contacts(contacts)

        if total == 0:
            return 0.0

        return (
            ContactKPI.total_missed(contacts)
            / total
        )