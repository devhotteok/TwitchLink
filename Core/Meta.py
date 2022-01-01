import datetime


class Meta:
    APP_NAME = "TwitchLink"

    VERSION = "1.1.0"

    AUTHOR = "DevHotteok"

    LICENSE = "MIT"

    FIRST_VERSION_RELEASED = datetime.date(2021, 2, 1)

    class CONTACT:
        DISCORD = ""
        EMAIL = ""

    HOMEPAGE_URL = "https://twitchlink.github.io/"

    @classmethod
    def getCopyrightInfo(cls):
        thisYear = datetime.datetime.now().year
        if cls.FIRST_VERSION_RELEASED.year < thisYear:
            year = "{}-{}".format(cls.FIRST_VERSION_RELEASED.year, thisYear)
        else:
            year = cls.FIRST_VERSION_RELEASED.year
        return "ⓒ {} {}.".format(year, cls.AUTHOR)

    @classmethod
    def getProjectInfo(cls):
        return "{}\n\n[Author]\n{}\n\n[License]\n{} License\n\n{}".format(cls.APP_NAME, cls.AUTHOR, cls.LICENSE, cls.getCopyrightInfo())


print(Meta.getProjectInfo())