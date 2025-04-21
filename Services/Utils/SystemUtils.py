from Core.Config import Config
from Services.Utils.OSUtils import OSUtils

from PyQt6 import QtCore

import platform


class SystemUtils:
    @staticmethod
    def getSystemLocale() -> QtCore.QLocale:
        return QtCore.QLocale.system()

    @staticmethod
    def getTimezone(timezoneId: bytes | QtCore.QByteArray) -> QtCore.QTimeZone:
        return QtCore.QTimeZone(timezoneId)

    @classmethod
    def getTimezoneNameList(cls) -> list[str]:
        return [cls.getTimezone(timezoneId).name() for timezoneId in QtCore.QTimeZone.availableTimeZoneIds()]

    @classmethod
    def getLocalTimezone(cls) -> QtCore.QTimeZone:
        return cls.getTimezone(QtCore.QTimeZone.systemTimeZoneId())

    @staticmethod
    def getUserAgent() -> str:
        appInfo = f"{Config.APP_NAME}/{Config.APP_VERSION}"
        if OSUtils.isWindows():
            version = ".".join(platform.win32_ver()[1].split(".")[:2])
            info1 = "Win64" if platform.architecture()[0] == "64bit" else "Win32"
            info2 = "x64" if platform.architecture()[0] == "64bit" else "x86"
            systemInfo = f"Windows NT {version}; {info1}; {info2}"
        else:
            systemInfo = f"Macintosh; Intel Mac OS X 10_15_7"
        userAgent = Config.USER_AGENT_TEMPLATE or "{appInfo} ({systemInfo})"
        try:
            return userAgent.format(appInfo=appInfo, systemInfo=systemInfo)
        except:
            return userAgent