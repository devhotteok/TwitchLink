from .SafeNetworkReply import SafeNetworkReply

from PyQt6 import QtCore, QtNetwork


class _QNetworkAccessManager(QtNetwork.QNetworkAccessManager):
    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.setTransferTimeout(QtNetwork.QNetworkRequest.TransferTimeoutConstant.DefaultTransferTimeoutConstant.value)
        self.setAutoDeleteReplies(True)

    def get(self, request: QtNetwork.QNetworkRequest) -> SafeNetworkReply:
        return SafeNetworkReply(request, super().get(request), parent=self)

    def post(self, request: QtNetwork.QNetworkRequest, data: QtCore.QByteArray) -> SafeNetworkReply:
        return SafeNetworkReply(request, super().post(request, data), parent=self)
QtNetwork.QNetworkAccessManager = _QNetworkAccessManager #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)