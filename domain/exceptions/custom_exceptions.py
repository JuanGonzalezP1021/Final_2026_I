class AppError(Exception):
    """Base exception for the application."""
    pass


class ValidationError(AppError):
    def __init__(self, field, message):
        super().__init__(f"{field}: {message}")


class BusinessRuleError(AppError):
    def __init__(self, rule_id, message):
        self.rule_id = rule_id
        super().__init__(f"{rule_id}: {message}")


class NotFoundError(AppError):
    def __init__(self, entity, key):
        super().__init__(f"{entity} '{key}' not found")


class DuplicateError(AppError):
    def __init__(self, entity, key):
        super().__init__(f"{entity} '{key}' already exists")


class IntegrityError(AppError):
    def __init__(self, message):
        super().__init__(message)