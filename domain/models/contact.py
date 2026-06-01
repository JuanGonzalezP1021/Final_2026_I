from dataclasses import dataclass


@dataclass
class Contact:
    contact_id: str
    agent_id: str
    date: str
    channel: str
    inbound_tx: int
    outbound_tx: int
    missed_tx: int
    handle_time_sec: int
    acw_sec: int

    @property
    def total_contacts(self) -> int:
        return (
            self.inbound_tx
            + self.outbound_tx
            + self.missed_tx
        )

    @property
    def aht(self) -> float:
        handled = self.inbound_tx + self.outbound_tx

        if handled == 0:
            return 0.0

        return (
            self.handle_time_sec
            + self.acw_sec
        ) / handled

    def to_dict(self):
        return {
            "contact_id": self.contact_id,
            "agent_id": self.agent_id,
            "date": self.date,
            "channel": self.channel,
            "inbound_tx": self.inbound_tx,
            "outbound_tx": self.outbound_tx,
            "missed_tx": self.missed_tx,
            "handle_time_sec": self.handle_time_sec,
            "acw_sec": self.acw_sec,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(**data)