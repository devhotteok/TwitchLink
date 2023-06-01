from Core.Config import Config

from PyQt6 import QtWebEngineCore

import re


class _QWebEngineProfile(QtWebEngineCore.QWebEngineProfile):
    def __init__(self, parent=None):
        super(_QWebEngineProfile, self).__init__(parent=parent)
        self.setupProfile()

    def setupProfile(self):
        self.setHttpUserAgent(re.sub("QtWebEngine/\S*", f"{Config.APP_NAME}/{Config.APP_VERSION}", self.httpUserAgent()))

    @classmethod
    def setup(cls):
        cls.defaultProfile().setPersistentCookiesPolicy(QtWebEngineCore.QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        cls.defaultProfile().clearAllVisitedLinks()
        cls.defaultProfile().cookieStore().deleteAllCookies()
        cls.setupProfile(cls.defaultProfile())
QtWebEngineCore.QWebEngineProfile = _QWebEngineProfile #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)