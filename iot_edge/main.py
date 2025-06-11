from domain.services.access_validator import AccessValidator
from infrastructure.persistence.sqlite_repo import SQLiteAccessRepository
from application.register_access import RegisterAccess
from infrastructure.messaging.mqtt_listener import MQTTListener

AUTHORIZED_USERS = ["alejandro", "carmen", "juan"]

if __name__ == "__main__":
    validator = AccessValidator(AUTHORIZED_USERS)
    repo = SQLiteAccessRepository()
    use_case = RegisterAccess(validator, repo)

    listener = MQTTListener(use_case)
    listener.start()
