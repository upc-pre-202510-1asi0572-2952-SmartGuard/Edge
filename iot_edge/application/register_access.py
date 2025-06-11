from iot_edge.domain.models.access_event import AccessEvent
from datetime import datetime

class RegisterAccess:
    def __init__(self, validator, repository):
        self.validator = validator
        self.repository = repository

    def execute(self, user_id: str, method: str = "FACE_RECOGNITION"):
        result = self.validator.validate(user_id)
        event = AccessEvent(
            user_id=user_id,
            timestamp=datetime.now(),
            result=result,
            method=method
        )
        self.repository.save(event)
        return event