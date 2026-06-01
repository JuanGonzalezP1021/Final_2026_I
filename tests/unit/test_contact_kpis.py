from domain.models.contact import Contact
from analytics.kpis.contact_kpis import ContactKPI


def build_contact(inbound, outbound, missed):
    return Contact(
        contact_id="C001",
        agent_id="A001",
        date="2026-06-01",
        channel="VOICE",
        inbound_tx=inbound,
        outbound_tx=outbound,
        missed_tx=missed,
        handle_time_sec=1000,
        acw_sec=200
    )


def test_total_contacts():
    contacts = [
        build_contact(10, 5, 2),
        build_contact(20, 10, 1)
    ]

    assert ContactKPI.total_contacts(contacts) == 48


def test_total_missed():
    contacts = [
        build_contact(10, 5, 2),
        build_contact(20, 10, 1)
    ]

    assert ContactKPI.total_missed(contacts) == 3


def test_average_aht():
    contacts = [
        build_contact(10, 10, 0)
    ]

    assert ContactKPI.average_aht(contacts) == 60