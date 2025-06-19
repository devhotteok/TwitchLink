from .BrowserCookieDetector import BrowserCookieDetector, BrowserProfile, Exceptions

from Services.Utils.OSUtils import OSUtils

import os
import configparser
import selenium.webdriver


class FirefoxCookieDetector(BrowserCookieDetector):
    @staticmethod
    def getDisplayName() -> str:
        return "Firefox"

    @staticmethod
    def _getLocalStatePath() -> str:
        if OSUtils.isWindows():
            return os.path.expandvars(r"%APPDATA%\Mozilla\Firefox\profiles.ini")
        else:
            return os.path.expanduser("~/Library/Application Support/Firefox/profiles.ini")

    @staticmethod
    def _getUserDataPath() -> str:
        if OSUtils.isWindows():
            return os.path.expandvars(r"%APPDATA%\Mozilla\Firefox")
        else:
            return os.path.expanduser("~/Library/Application Support/Firefox")

    @staticmethod
    def _createDriver(userDataPath: str, profileKey: str) -> selenium.webdriver.Firefox:
        options = selenium.webdriver.FirefoxOptions()
        options.profile = selenium.webdriver.FirefoxProfile(os.path.join(userDataPath, profileKey))
        options.add_argument("-headless")
        return selenium.webdriver.Firefox(options=options)

    @classmethod
    def getProfiles(cls) -> list[BrowserProfile]:
        try:
            parser = configparser.ConfigParser()
            parser.read(cls._getLocalStatePath(), encoding="utf-8")
            return [
                BrowserProfile(
                    browserName=cls.getDisplayName(),
                    key=parser.get(section, "Path") or "",
                    displayName=parser.get(section, "Name") or ""
                ) for section in parser.sections() if section.lower().startswith("profile")
            ]
        except:
            raise Exceptions.BrowserNotFound()