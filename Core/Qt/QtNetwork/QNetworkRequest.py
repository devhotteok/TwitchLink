from Services.Utils.SystemUtils import SystemUtils

from PyQt6 import QtNetwork


class _QNetworkRequest(QtNetwork.QNetworkRequest):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.UserAgentHeader, SystemUtils.getUserAgent())
        self.setTransferTimeout(QtNetwork.QNetworkRequest.TransferTimeoutConstant.DefaultTransferTimeoutConstant.value)
QtNetwork.QNetworkRequest = _QNetworkRequest #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)