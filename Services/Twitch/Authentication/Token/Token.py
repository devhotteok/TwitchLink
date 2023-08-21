from AppData.EncoderDecoder import Serializable

from PyQt6 import QtCore


class Exceptions:
    class InvalidToken(Exception):
        def __str__(self):
            return "Invalid Token"


class Token(Serializable):
    SERIALIZABLE_INIT_MODEL = False
    SERIALIZABLE_STRICT_MODE = False

    def __init__(self, value: str, expiration: int | None = None):
        self.value = value
        self.expiration = None if expiration == None else QtCore.QDateTime.fromSecsSinceEpoch(expiration, QtCore.Qt.TimeSpec.UTC)

    def isValid(self) -> bool:
        return not self.isExpired()

    def isExpired(self) -> bool:
        if self.expiration == None:
            return False
        return QtCore.QDateTime.currentDateTimeUtc() > self.expiration

    def validate(self) -> None:
        if self.isExpired():
            raise Exceptions.InvalidToken