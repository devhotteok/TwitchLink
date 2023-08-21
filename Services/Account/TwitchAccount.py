from Core import App
from Services.Twitch.Authentication.OAuth.OAuthToken import OAuthToken
from Services.Twitch.GQL import TwitchGQLModels
from AppData.EncoderDecoder import Serializable

from PyQt6 import QtCore

import typing


class TwitchAccount(QtCore.QObject, Serializable):
    SERIALIZABLE_INIT_MODEL = False
    SERIALIZABLE_STRICT_MODE = False

    accountUpdated = QtCore.pyqtSignal()
    authorizationExpired = QtCore.pyqtSignal()

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.clearData()

    def login(self, user: TwitchGQLModels.User, token: str, expiration: int | None = None) -> None:
        if self.isLoggedIn():
            self.logout()
        self.user = user
        self.oAuthToken = OAuthToken(token, expiration)
        self.updateIntegrityToken()
        self.accountUpdated.emit()

    def logout(self) -> None:
        self.clearData()
        self.updateIntegrityToken()
        self.accountUpdated.emit()

    def invalidate(self) -> None:
        self.logout()
        self.authorizationExpired.emit()

    def setData(self, user: TwitchGQLModels.User | None, oAuthToken: OAuthToken | None) -> None:
        self.user = user
        self.oAuthToken = oAuthToken

    def getData(self) -> tuple[TwitchGQLModels.User, OAuthToken]:
        return self.user, self.oAuthToken

    def clearData(self) -> None:
        self.user = None
        self.oAuthToken = None

    def isLoggedIn(self) -> bool:
        return self.user != None

    def validateOAuthToken(self) -> None:
        if self.isLoggedIn():
            try:
                self.oAuthToken.validate()
            except:
                self.invalidate()

    def getOAuthToken(self) -> str:
        self.validateOAuthToken()
        if self.oAuthToken == None:
            return ""
        else:
            return self.oAuthToken.value

    def updateIntegrityToken(self) -> None:
        App.TwitchIntegrityGenerator.updateIntegrity(forceUpdate=True)

    def getIntegrityToken(self, callback: typing.Callable) -> None:
        App.TwitchIntegrityGenerator.getIntegrity(callback)