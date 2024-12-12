from PyQt6 import QtCore


class Meta:
    APP_NAME = "TwitchLink"

    APP_VERSION = "3.2.1"

    AUTHOR = "DevHotteok"

    FIRST_VERSION_RELEASED_YEAR = 2021

    CONTACT = {}

    HOMEPAGE_URL = "https://twitchlink.github.io/"

    @classmethod
    def getCopyrightInfo(cls) -> str:
        return f"ⓒ {max(cls.FIRST_VERSION_RELEASED_YEAR, QtCore.QDate().currentDate().year())} {cls.AUTHOR}."

    @classmethod
    def getProjectInfo(cls) -> str:
        return f"{cls.APP_NAME} {cls.APP_VERSION}\n\n{cls.getCopyrightInfo()}"