from PyQt6 import QtCore, QtNetwork


class _QNetworkAccessManager(QtNetwork.QNetworkAccessManager):
    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.setTransferTimeout(QtNetwork.QNetworkRequest.TransferTimeoutConstant.DefaultTransferTimeoutConstant.value)
        self.setAutoDeleteReplies(True)
QtNetwork.QNetworkAccessManager = _QNetworkAccessManager #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)