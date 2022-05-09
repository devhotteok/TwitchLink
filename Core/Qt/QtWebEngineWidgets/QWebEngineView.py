from Core.Config import Config

from PyQt5 import QtCore, QtWidgets, QtWebEngineWidgets

import re


class _QWebEngineView(QtWebEngineWidgets.QWebEngineView):
    needProfileSetup = True

    def __init__(self, parent=None):
        super(_QWebEngineView, self).__init__(parent=parent)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        if _QWebEngineView.needProfileSetup:
            profile = QtWebEngineWidgets.QWebEngineProfile.defaultProfile()
            profile.setHttpUserAgent(re.sub("QtWebEngine/\S*", f"{Config.APP_NAME}/{Config.VERSION}", profile.httpUserAgent()))
            _QWebEngineView.needProfileSetup = False

    def dropEvent(self, event):
        event.ignore()
QtWebEngineWidgets.QWebEngineView = _QWebEngineView