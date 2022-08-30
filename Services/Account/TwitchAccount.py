from Database.EncoderDecoder import Codable
from Search import Engine

from PyQt5 import QtCore


class Exceptions:
    class InvalidToken(Exception):
        def __str__(self):
            return "Invalid Token"

    class UserNotFound(Exception):
        def __str__(self):
            return "User Not Found"


class TwitchAccount(QtCore.QObject, Codable):
    accountUpdated = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(TwitchAccount, self).__init__(parent=parent)
        self.logout()

    def login(self, username, token, expiry=None):
        if self.isConnected():
            self.logout()
        self.username = username
        self.token = token
        self.expiry = expiry
        self.updateAccount()

    def logout(self):
        self.clearData()
        self.accountUpdated.emit()

    def clearData(self):
        self.username = None
        self.token = ""
        self.expiry = None
        self.data = None

    def isConnected(self):
        return self.username != None

    def checkToken(self):
        if self.expiry != None:
            if QtCore.QDateTime.currentDateTimeUtc() > self.expiry:
                self.logout()
                raise Exceptions.InvalidToken

    def updateAccount(self):
        self.checkToken()
        self.updateAccountData()
        self.accountUpdated.emit()

    def updateAccountData(self):
        if self.isConnected():
            try:
                data = Engine.Search.Channel(self.username)
                data.stream = None
                self.data = data
            except Engine.Exceptions.ChannelNotFound:
                self.logout()
                raise Exceptions.UserNotFound