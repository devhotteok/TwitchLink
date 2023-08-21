from ..Token.Token import Token


class IntegrityToken(Token):
    def __init__(self, headers: dict, value: str, expiration: int | None = None):
        super().__init__(value, expiration)
        self.headers = headers

    def getHeaders(self) -> dict:
        return self.headers | {"Client-Integrity": self.value}