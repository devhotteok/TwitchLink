from .BrowserCookieDetector import BrowserCookieDetector

from Services.Utils.OSUtils import OSUtils

import os
import selenium.webdriver


class EdgeCookieDetector(BrowserCookieDetector):
    @staticmethod
    def getDisplayName() -> str:
        return "Edge"

    @staticmethod
    def _getLocalStatePath() -> str:
        if OSUtils.isWindows():
            return os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data\Local State")
        else:
            return os.path.expanduser("~/Library/Application Support/Microsoft Edge/Local State")

    @staticmethod
    def _getUserDataPath() -> str:
        if OSUtils.isWindows():
            return os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\User Data")
        else:
            return os.path.expanduser("~/Library/Application Support/Microsoft Edge")

    @staticmethod
    def _createDriver(userDataPath: str, profileKey: str) -> selenium.webdriver.Edge:
        options = selenium.webdriver.EdgeOptions()
        options.add_argument(f"--user-data-dir={userDataPath}")
        options.add_argument(f"--profile-directory={profileKey}")
        options.add_argument("--headless=new")
        return selenium.webdriver.Edge(options=options)