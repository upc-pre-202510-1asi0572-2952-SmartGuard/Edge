class AccessValidator:
    def __init__(self, authorized_users: list[str]):
        self.authorized_users = authorized_users
    def validate(self, user_id: str) -> str:
        return "GRANTED" if user_id in self.authorized_users else "DENIED"