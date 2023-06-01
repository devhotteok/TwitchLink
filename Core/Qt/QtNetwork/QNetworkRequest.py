from Core.Config import Config

from PyQt6 import QtNetwork


class _QNetworkRequest(QtNetwork.QNetworkRequest):
    def __init__(self, *args, **kwargs):
        super(_QNetworkRequest, self).__init__(*args, **kwargs)
        self.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.UserAgentHeader, f"{Config.APP_NAME}/{Config.APP_VERSION}")
QtNetwork.QNetworkRequest = _QNetworkRequest #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)