from Core.Config import Config

from PyQt6 import QtWebEngineCore

import re


class _QWebEngineProfile(QtWebEngineCore.QWebEngineProfile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setupProfile()

    def _setupProfile(self) -> None:
        formatString = re.sub("QtWebEngine/\S*", "{appInfo}", self.httpUserAgent()) if Config.USER_AGENT_FORMAT == None else Config.USER_AGENT_FORMAT
        userAgent = formatString.format(appInfo=f"{Config.APP_NAME}/{Config.APP_VERSION}")
        self.setHttpUserAgent(userAgent)

    @classmethod
    def setup(cls) -> None:
        cls.defaultProfile().setPersistentCookiesPolicy(QtWebEngineCore.QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        cls.defaultProfile().clearAllVisitedLinks()
        cls.defaultProfile().cookieStore().deleteAllCookies()
        cls._setupProfile(cls.defaultProfile())
QtWebEngineCore.QWebEngineProfile = _QWebEngineProfile #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)