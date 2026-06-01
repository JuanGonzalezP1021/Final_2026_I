from abc import ABC, abstractmethod
from datetime import datetime
from infrastructure.services.logger import audit_log
from config import EMAIL_SENDER, EMAIL_RECIPIENTS

class NotificationService(ABC):
    @abstractmethod
    def notify(self, operation: str, entity: str, payload: dict) -> dict:
        ...

class ConsoleNotification(NotificationService):
    def notify(self, operation, entity, payload):
        msg = {
            'ts': datetime.now().isoformat(),
            'op': operation, 
            'entity': entity
        }
        print(f"[{msg['ts']}] {operation} {entity}")
        return msg

class NotificationDecorator(NotificationService):
    def __init__(self, wrapped: NotificationService):
        self._wrapped = wrapped

    def notify(self, operation, entity, payload):
        return self._wrapped.notify(operation, entity, payload)

class TimestampDecorator(NotificationDecorator):
    def notify(self, operation, entity, payload):
        payload = {**payload, '_ts': datetime.now().isoformat()}
        return super().notify(operation, entity, payload)

class EmailNotificationDecorator(NotificationDecorator):
    def notify(self, operation, entity, payload):
        base = super().notify(operation, entity, payload)
        envelope = {
            'from': EMAIL_SENDER,
            'to': EMAIL_RECIPIENTS,
            'subject': f'[CallCenter] {operation} on {entity}',
            'body': f'Operation: {operation}\nEntity: {entity}\n'
                    f'Payload: {payload}'
        }
        self._send(envelope)
        return {**base, 'email': envelope}

    def _send(self, envelope):  # simulated SMTP
        print(f"MAIL -> {envelope['to']}: {envelope['subject']}")

class AuditLogDecorator(NotificationDecorator):
    def notify(self, operation, entity, payload):
        audit_log(operation, entity, payload)
        return super().notify(operation, entity, payload)

def default_notifier() -> NotificationService:
    """Factory: AuditLog(Email(Timestamp(Console)))"""
    return AuditLogDecorator(
        EmailNotificationDecorator(
            TimestampDecorator(
                ConsoleNotification()
            )
        )
    )