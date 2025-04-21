from .BrowserCookieDetector import BrowserCookieDetector

from Services.Utils.OSUtils import OSUtils

import os
import selenium.webdriver


class ChromeCookieDetector(BrowserCookieDetector):
    @staticmethod
    def getDisplayName() -> str:
        return "Chrome"

    @staticmethod
    def _getLocalStatePath() -> str:
        if OSUtils.isWindows():
            return os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data\Local State")
        else:
            return os.path.expanduser("~/Library/Application Support/Google/Chrome/Local State")

    @staticmethod
    def _getUserDataPath() -> str:
        if OSUtils.isWindows():
            return os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\User Data")
        else:
            return os.path.expanduser("~/Library/Application Support/Google/Chrome")

    @staticmethod
    def _createDriver(userDataPath: str, profileKey: str) -> selenium.webdriver.Chrome:
        options = selenium.webdriver.ChromeOptions()
        options.add_argument(f"--user-data-dir={userDataPath}")
        options.add_argument(f"--profile-directory={profileKey}")
        options.add_argument("--headless=new")
        return selenium.webdriver.Chrome(options=options)