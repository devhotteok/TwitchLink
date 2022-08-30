from Core.Config import Config

from PyQt5 import QtWebEngineWidgets

import re


class _QWebEngineProfile(QtWebEngineWidgets.QWebEngineProfile):
    def __init__(self, parent=None):
        super(_QWebEngineProfile, self).__init__(parent=parent)
        self.setupProfile()

    def setupProfile(self):
        self.setHttpUserAgent(re.sub("QtWebEngine/\S*", f"{Config.APP_NAME}/{Config.VERSION}", self.httpUserAgent()))

    @classmethod
    def setup(cls):
        cls.defaultProfile().clearAllVisitedLinks()
        cls.defaultProfile().cookieStore().deleteAllCookies()
        cls.setupProfile(cls.defaultProfile())
QtWebEngineWidgets.QWebEngineProfile = _QWebEngineProfile #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)