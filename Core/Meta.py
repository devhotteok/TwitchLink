import datetime


class Meta:
    APP_NAME = "TwitchLink"

    VERSION = "2.1.0"

    AUTHOR = "DevHotteok"

    LICENSE = "MIT"

    FIRST_VERSION_RELEASED = datetime.date(2021, 2, 1)

    class CONTACT:
        DISCORD = ""
        EMAIL = ""

    HOMEPAGE_URL = "https://twitchlink.github.io/"

    @classmethod
    def getCopyrightInfo(cls):
        return f"ⓒ {max(cls.FIRST_VERSION_RELEASED.year, datetime.datetime.now().year)} {cls.AUTHOR}."

    @classmethod
    def getProjectInfo(cls):
        return f"{cls.APP_NAME} {cls.VERSION}\n\n[Author]\n{cls.AUTHOR}\n\n[License]\n{cls.LICENSE} License\n\n{cls.getCopyrightInfo()}"