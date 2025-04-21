from .Config import Config
from .AccountData import AccountData
from .BrowserCookieDetector.BrowserCookieDetector import BrowserCookieDetector, BrowserProfile, Exceptions as BrowserCookieDetectorExceptions
from .BrowserCookieDetector.ChromeCookieDetector import ChromeCookieDetector
from .BrowserCookieDetector.EdgeCookieDetector import EdgeCookieDetector

from PyQt6 import QtCore


class Exceptions(BrowserCookieDetectorExceptions):
    class AccountNotFound(Exception):
        def __str__(self):
            return "Account Not Found"


class BrowserInfo:
    def __init__(self, cookieDetector: type[BrowserCookieDetector]):
        self._cookieDetector = cookieDetector

    def getDisplayName(self) -> str:
        return self._cookieDetector.getDisplayName()

    def getCookieDetector(self) -> type[BrowserCookieDetector]:
        return self._cookieDetector


class AvailableBrowsers:
    Chrome = BrowserInfo(cookieDetector=ChromeCookieDetector)
    Edge = BrowserInfo(cookieDetector=EdgeCookieDetector)


class BrowserAccountDetectorThread(QtCore.QThread):
    browserProfileUpdated = QtCore.pyqtSignal(BrowserProfile)

    def __init__(self, browserCookieDetector: type[BrowserCookieDetector], profile: BrowserProfile | None = None, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._browserCookieDetector = browserCookieDetector
        self._profile = profile
        self._accountData: AccountData | None = None
        self._exception: Exceptions.BrowserNotFound | Exceptions.DriverConnectionFailure | Exceptions.UnexpectedDriverError | None = None
        self._cancelRequested: bool = False

    def getAccountData(self) -> AccountData | None:
        return self._accountData

    def getException(self) -> Exceptions.BrowserNotFound | Exceptions.DriverConnectionFailure | Exceptions.UnexpectedDriverError | None:
        return self._exception

    def run(self) -> None:
        try:
            profiles = self._browserCookieDetector.getProfiles() if self._profile == None else [self._profile]
            for profile in profiles:
                self.browserProfileUpdated.emit(profile)
                cookies = self._browserCookieDetector.getProfileCookies(
                    url=Config.LOGIN_PAGE,
                    domain=Config.COOKIE_DOMAIN,
                    profile=profile,
                    names=[
                        Config.COOKIE_USERNAME,
                        Config.COOKIE_AUTH_TOKEN
                    ]
                )
                if self._cancelRequested:
                    break
                usernameCookie = cookies.get(Config.COOKIE_USERNAME)
                authTokenCookie = cookies.get(Config.COOKIE_AUTH_TOKEN)
                if usernameCookie != None and authTokenCookie != None:
                    self._accountData = AccountData(
                        username=usernameCookie.value,
                        token=authTokenCookie.value,
                        expiration=authTokenCookie.expiry
                    )
                    break
        except Exception as e:
            self._exception = e

    def cancel(self) -> None:
        self._cancelRequested = True


class BrowserAccountDetector(QtCore.QObject):
    browserProfileUpdated = QtCore.pyqtSignal(BrowserProfile)
    accountDetected = QtCore.pyqtSignal(AccountData)
    errorOccurred = QtCore.pyqtSignal(Exception)
    finished = QtCore.pyqtSignal()

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._thread: BrowserAccountDetectorThread | None = None

    def getProfiles(self, browserInfo: BrowserInfo) -> list[BrowserProfile]:
        return browserInfo.getCookieDetector().getProfiles()

    def importAccount(self, browserInfo: BrowserInfo, profile: BrowserProfile | None = None) -> None:
        if self.isRunning():
            return
        self._thread = BrowserAccountDetectorThread(browserCookieDetector=browserInfo.getCookieDetector(), profile=profile, parent=self)
        self._thread.browserProfileUpdated.connect(self.browserProfileUpdated)
        self._thread.finished.connect(self._finished)
        self._thread.start()

    def _finished(self) -> None:
        if self._thread.getAccountData() != None:
            self.accountDetected.emit(self._thread.getAccountData())
        elif self._thread.getException() != None:
            self.errorOccurred.emit(self._thread.getException())
        else:
            self.errorOccurred.emit(Exceptions.AccountNotFound())
        self._thread.deleteLater()
        self._thread = None
        self.finished.emit()

    def isRunning(self) -> bool:
        return self._thread != None

    def abort(self) -> None:
        if self.isRunning():
            self._thread.cancel()