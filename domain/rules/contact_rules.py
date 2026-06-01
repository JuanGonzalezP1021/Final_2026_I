from config import (
    MAX_CONTACTS_PER_AGENT_DAY,
    MISSED_THRESHOLD_PER_DAY
)

from domain.exceptions.custom_exceptions import (
    BusinessRuleError
)


def validate_contact_volume(contact):
    total_handled = (
        contact.inbound_tx
        + contact.outbound_tx
    )

    if total_handled > MAX_CONTACTS_PER_AGENT_DAY:
        raise BusinessRuleError(
            "BR-05",
            f"Agent exceeds {MAX_CONTACTS_PER_AGENT_DAY} contacts per day"
        )


def validate_missed_contacts(contact):
    if contact.missed_tx > MISSED_THRESHOLD_PER_DAY:
        raise BusinessRuleError(
            "BR-06",
            f"Missed contacts exceed {MISSED_THRESHOLD_PER_DAY}"
        )


def validate_contact(contact):
    validate_contact_volume(contact)
    validate_missed_contacts(contact)