from Core import App

from PyQt6 import QtCore, QtGui, QtNetwork

import typing


class ImageRequest(QtCore.QObject):
    urlLoaded = QtCore.pyqtSignal(QtCore.QUrl)
    imageLoaded = QtCore.pyqtSignal(QtGui.QPixmap)

    def __init__(self, reply: QtNetwork.QNetworkReply, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._clients = 0
        self._reply = reply
        self._reply.finished.connect(self._requestDone)

    def connect(self, callback: typing.Callable) -> None:
        self.imageLoaded.connect(callback)
        self._clients += 1

    def disconnect(self, callback: typing.Callable) -> None:
        self.imageLoaded.disconnect(callback)
        self._clients -= 1
        if self._clients == 0:
            self._reply.abort()

    def _requestDone(self) -> None:
        pixmap = QtGui.QPixmap()
        if self._reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            pixmap.loadFromData(self._reply.readAll().data())
        self.urlLoaded.emit(self._reply.request().url())
        self.imageLoaded.emit(pixmap)
        self.deleteLater()


class ImageLoader(QtCore.QObject):
    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._requests = {}

    def request(self, url: QtCore.QUrl, callback: typing.Callable, refresh: bool = False) -> None:
        if not self._hasRequest(url):
            networkRequest = QtNetwork.QNetworkRequest(url)
            networkRequest.setPriority(QtNetwork.QNetworkRequest.Priority.LowPriority)
            if refresh:
                networkRequest.setAttribute(QtNetwork.QNetworkRequest.Attribute.CacheLoadControlAttribute, QtNetwork.QNetworkRequest.CacheLoadControl.AlwaysNetwork)
            request = ImageRequest(reply=App.NetworkAccessManager.get(networkRequest), parent=self)
            request.urlLoaded.connect(self._urlLoaded)
            self._requests[url] = request
        self._getRequest(url).connect(callback)

    def cancelRequest(self, url: QtCore.QUrl, callback: typing.Callable) -> None:
        if self._hasRequest(url):
            self._getRequest(url).disconnect(callback)

    def _urlLoaded(self, url: QtCore.QUrl) -> None:
        self._requests.pop(url)

    def _hasRequest(self, url: QtCore.QUrl) -> bool:
        return url in self._requests

    def _getRequest(self, url: QtCore.QUrl) -> ImageRequest:
        return self._requests[url]