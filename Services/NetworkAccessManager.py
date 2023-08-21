from Core.Config import Config
from Services.Utils.OSUtils import OSUtils

from PyQt6 import QtCore, QtNetwork


class NetworkAccessManager(QtNetwork.QNetworkAccessManager):
    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        cache = QtNetwork.QNetworkDiskCache()
        cache.setCacheDirectory(OSUtils.joinPath(Config.TEMP_PATH, "cache"))
        self.setCache(cache)