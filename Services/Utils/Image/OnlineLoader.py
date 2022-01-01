from Core.GlobalExceptions import Exceptions
from Services.NetworkRequests import requests

from PyQt5 import QtCore, QtGui


class OnlineLoader(QtCore.QThread):
    _imageSender = QtCore.pyqtSignal(object)
    _loaded = QtCore.pyqtSignal(str)

    def __init__(self, url, callback):
        super().__init__()
        self._url = url
        self._result = None
        self._loaded.connect(callback)
        self.start()

    def reserve(self, callback):
        self._imageSender.connect(callback)

    def processReservedEvents(self):
        self._imageSender.emit(self._result)

    def run(self):
        try:
            self._result = self.load()
        except:
            pass
        self._loaded.emit(self._url)

    def load(self):
        try:
            data = requests.get(self._url)
            if data.status_code == 200:
                image = QtGui.QImage()
                image.loadFromData(data.content)
                return QtGui.QPixmap(image)
            else:
                raise
        except:
            raise Exceptions.NetworkError