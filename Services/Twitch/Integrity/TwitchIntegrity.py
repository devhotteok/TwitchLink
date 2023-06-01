from PyQt6 import QtCore


class Integrity:
    def __init__(self, headers, token, expiration=None):
        self.headers = headers
        self.token = token
        self.expiration = None if expiration == None else QtCore.QDateTime.fromSecsSinceEpoch(expiration, QtCore.Qt.TimeSpec.UTC)
        self.headers.update({"Client-Integrity": self.token})

    def isValid(self):
        return not self.isExpired()

    def isExpired(self):
        return QtCore.QDateTime.currentDateTimeUtc() > self.expiration

    def getHeaders(self):
        return self.headers