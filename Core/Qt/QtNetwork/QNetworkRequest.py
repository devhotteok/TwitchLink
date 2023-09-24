from Core.Config import Config

from PyQt6 import QtNetwork


class _QNetworkRequest(QtNetwork.QNetworkRequest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        formatString = "{appInfo}" if Config.USER_AGENT_FORMAT == None else Config.USER_AGENT_FORMAT
        userAgent = formatString.format(appInfo=f"{Config.APP_NAME}/{Config.APP_VERSION}")
        self.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.UserAgentHeader, userAgent)
        self.setTransferTimeout(QtNetwork.QNetworkRequest.TransferTimeoutConstant.DefaultTransferTimeoutConstant.value)
QtNetwork.QNetworkRequest = _QNetworkRequest #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)