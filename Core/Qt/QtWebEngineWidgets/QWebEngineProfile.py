from Services.Utils.SystemUtils import SystemUtils

from PyQt6 import QtWebEngineCore


class _QWebEngineProfile(QtWebEngineCore.QWebEngineProfile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._setupProfile()

    def _setupProfile(self) -> None:
        import re
        self.setHttpUserAgent(re.sub(r"QtWebEngine/[\d\.]+\s*", "", self.httpUserAgent()))
        self.setHttpAcceptLanguage("en-US,en;q=0.9")
        script = QtWebEngineCore.QWebEngineScript()
        script.setSourceCode("Object.defineProperty(navigator, 'webdriver', { get: () => undefined }); window.chrome = { runtime: {} };")
        script.setWorldId(QtWebEngineCore.QWebEngineScript.ScriptWorldId.MainWorld)
        script.setInjectionPoint(QtWebEngineCore.QWebEngineScript.InjectionPoint.DocumentCreation)
        self.scripts().insert(script)

    @classmethod
    def setup(cls) -> None:
        cls.defaultProfile().setPersistentCookiesPolicy(QtWebEngineCore.QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies)
        cls.defaultProfile().clearAllVisitedLinks()
        cls.defaultProfile().cookieStore().deleteAllCookies()
        cls._setupProfile(cls.defaultProfile())
QtWebEngineCore.QWebEngineProfile = _QWebEngineProfile #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)