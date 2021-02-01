from PyQt5 import uic

from TwitchLinkConfig import Config


class UiLoader:
    TRANSLATION_LIST = ["mainWindow", "loading", "settings", "login", "about", "termsOfService", "mainMenu", "search", "videoFrame", "videoBox", "videoList", "downloadMenu", "download"]

    def __init__(self):
        self.mainWindow = self.loadUi("mainWindow")
        self.loading = self.loadUi("loading")
        self.settings = self.loadUi("settings")
        self.login = self.loadUi("login")
        self.about = self.loadUi("about")
        self.termsOfService = self.loadUi("termsOfService")
        self.mainMenu = self.loadUi("mainMenu")
        self.search = self.loadUi("search")
        self.videoFrame = self.loadUi("videoFrame")
        self.videoBox = self.loadUi("videoBox")
        self.videoList = self.loadUi("videoList")
        self.downloadMenu = self.loadUi("downloadMenu")
        self.download = self.loadUi("download")

    def loadUi(self, ui_name):
        return uic.loadUiType(Config.UI_ROOT + "/" + ui_name + ".ui")[0]

uiLoader = UiLoader()