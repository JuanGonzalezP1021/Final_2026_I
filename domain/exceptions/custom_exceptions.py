class CallCenterError(Exception):
    '''Base class for all domain errors.'''
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.message = message
        self.code = code

class ValidationError(CallCenterError):
    def __init__(self, field, reason):
        super().__init__(f'Invalid {field}: {reason}', 'VALIDATION')
        self.field = field

class NotFoundError(CallCenterError):
    def __init__(self, entity, key):
        super().__init__(f'{entity} not found: {key}', 'NOT_FOUND')

class DuplicateError(CallCenterError):
    def __init__(self, entity, key):
        super().__init__(f'{entity} already exists: {key}', 'DUPLICATE')

class BusinessRuleError(CallCenterError):
    def __init__(self, rule_id, detail):
        super().__init__(f'[{rule_id}] {detail}', 'RULE_VIOLATION')
        self.rule_id = rule_id

class IntegrityError(CallCenterError):
    def __init__(self, detail):
        super().__init__(f'Referential integrity: {detail}', 'INTEGRITY')

class PersistenceError(CallCenterError):
    def __init__(self, operation, detail):
super().__init__(f'{operation} failed: {detail}', 'PERSISTENCE')