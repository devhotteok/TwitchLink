from PyQt5 import QtCore


class Meta:
    APP_NAME = "TwitchLink"

    APP_VERSION = "2.3.1"

    AUTHOR = "DevHotteok"

    LICENSE = "MIT"

    FIRST_VERSION_RELEASED = QtCore.QDate(2021, 2, 1)

    CONTACT = {}

    HOMEPAGE_URL = "https://twitchlink.github.io/"

    @classmethod
    def getCopyrightInfo(cls):
        return f"ⓒ {max(cls.FIRST_VERSION_RELEASED.year(), QtCore.QDate().currentDate().year())} {cls.AUTHOR}."

    @classmethod
    def getProjectInfo(cls):
        return f"{cls.APP_NAME} {cls.APP_VERSION}\n\n[Author]\n{cls.AUTHOR}\n\n[License]\n{cls.LICENSE} License\n\n{cls.getCopyrightInfo()}"