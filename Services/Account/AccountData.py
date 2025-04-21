class AccountData:
    def __init__(self, username: str | None = None, token: str | None = None, expiration: int | None = None):
        self.username = username
        self.token = token
        self.expiration = expiration