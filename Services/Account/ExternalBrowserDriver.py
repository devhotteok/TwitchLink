from .Config import Config
from .AccountData import AccountData

from Services.Logging.Logger import Logger

from PyQt6 import QtCore

from patchright.sync_api import sync_playwright
from patchright._impl._errors import TargetClosedError, TimeoutError

import gc


class BrowserInfo:
    def __init__(self, displayName: str, channel: str):
        self._displayName = displayName
        self._channel = channel

    def getDisplayName(self) -> str:
        return self._displayName

    def getChannel(self) -> str:
        return self._channel


class AvailableBrowsers:
    Chrome = BrowserInfo(displayName="Chrome", channel="chrome")
    Edge = BrowserInfo(displayName="Edge", channel="msedge")


class ExternalBrowserDriverThread(QtCore.QThread):
    def __init__(self, browserInfo: BrowserInfo, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._browserInfo = browserInfo
        self.logger = logger
        self._accountData: AccountData | None = None
        self._cancelRequested: bool = False
        self._errorOccurred: bool = False

    def getBrowserInfo(self) -> BrowserInfo:
        return self._browserInfo

    def getAccountData(self) -> AccountData | None:
        return self._accountData

    def hasError(self) -> bool:
        return self._errorOccurred

    def run(self) -> None:
        try:
            with sync_playwright() as playwright:
                context = playwright.chromium.launch_persistent_context(
                    user_data_dir="",
                    channel=self._browserInfo.getChannel(),
                    headless=False,
                    no_viewport=True,
                    args=["--start-maximized"]
                )
                page = context.new_page() if len(context.pages) == 0 else context.pages[0]
                page.bring_to_front()
                page.evaluate(f"location.replace('{Config.SIGN_IN_PAGE_URL}');")
                exitLoop = False
                while exitLoop == False:
                    try:
                        page.wait_for_function(
                            expression=f"""
                                () => {{
                                    if (location.hostname.endsWith("{Config.COOKIE_DOMAIN}") || location.hostname === "{Config.COOKIE_DOMAIN.lstrip(".")}") {{
                                        const cookies = document.cookie.split(";").map(c => c.trim().split("=")[0]);
                                        return cookies.includes("{Config.COOKIE_USERNAME}") && cookies.includes("{Config.COOKIE_AUTH_TOKEN}");
                                    }}
                                    return false;
                                }}
                            """,
                            timeout=100
                        )
                        break
                    except Exception as e:
                        if not isinstance(e, TimeoutError) or self._cancelRequested:
                            exitLoop = True
                cookies = context.cookies()
                usernameCookie = next((item for item in cookies if item["name"] == Config.COOKIE_USERNAME), None)
                authTokenCookie = next((item for item in cookies if item["name"] == Config.COOKIE_AUTH_TOKEN), None)
                if usernameCookie != None and authTokenCookie != None:
                    self._accountData = AccountData(
                        username=usernameCookie["value"],
                        token=authTokenCookie["value"],
                        expiration=authTokenCookie.get("expires", None)
                    )
                page.close()
                context.close()
        except Exception as e:
            if not isinstance(e, TargetClosedError):
                self._errorOccurred = True
            self.logger.error(f"An unexpected error occurred while launching {self._browserInfo.getDisplayName()}.")
            self.logger.exception(e)
        finally:
            gc.collect()

    def cancel(self) -> None:
        self._cancelRequested = True


class ExternalBrowserDriver(QtCore.QObject):
    accountDetected = QtCore.pyqtSignal(AccountData)
    errorOccurred = QtCore.pyqtSignal(BrowserInfo)
    finished = QtCore.pyqtSignal()

    def __init__(self, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.logger = logger
        self._thread: ExternalBrowserDriverThread | None = None

    def launch(self, browserInfo: BrowserInfo) -> None:
        if self.isRunning():
            return
        self._thread = ExternalBrowserDriverThread(browserInfo=browserInfo, logger=self.logger, parent=self)
        self._thread.finished.connect(self._finished)
        self._thread.start()

    def _finished(self) -> None:
        if self._thread.getAccountData() != None:
            self.accountDetected.emit(self._thread.getAccountData())
        elif self._thread.hasError():
            self.errorOccurred.emit(self._thread.getBrowserInfo())
        self._thread.deleteLater()
        self._thread = None
        self.finished.emit()

    def isRunning(self) -> bool:
        return self._thread != None

    def abort(self) -> None:
        if self.isRunning():
            self._thread.cancel()