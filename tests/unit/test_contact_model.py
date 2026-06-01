from domain.models.contact import Contact


def test_total_contacts():
    contact = Contact(
        contact_id="C001",
        agent_id="A001",
        date="2026-06-01",
        channel="VOICE",
        inbound_tx=10,
        outbound_tx=5,
        missed_tx=2,
        handle_time_sec=600,
        acw_sec=120
    )

    assert contact.total_contacts == 17


def test_aht():
    contact = Contact(
        contact_id="C001",
        agent_id="A001",
        date="2026-06-01",
        channel="VOICE",
        inbound_tx=10,
        outbound_tx=10,
        missed_tx=0,
        handle_time_sec=1000,
        acw_sec=200
    )

    assert contact.aht == 60