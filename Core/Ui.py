from Core.GlobalExceptions import Exceptions
from Core.Config import Config
from Services.Utils.Utils import Utils
from Services.Image.Presets import *
from Services.Translator.Translator import Translator, T
from Services.Ad import AdManager
from Database.Database import DB

from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, uic


class WindowGeometryManager:
    def __init__(self):
        super(WindowGeometryManager, self).__init__()
        self.setWindowGeometryKey()

    def setWindowGeometryKey(self, key=None):
        self.windowGeometryKey = key or self.__class__.__name__

    def getWindowGeometryKey(self):
        return self.windowGeometryKey

    def loadWindowGeometry(self):
        if DB.temp.hasWindowGeometry(self.windowGeometryKey):
            self.restoreGeometry(QtCore.QByteArray.fromBase64(DB.temp.getWindowGeometry(self.windowGeometryKey)))

    def saveWindowGeometry(self):
        DB.temp.setWindowGeometry(self.windowGeometryKey, self.saveGeometry().toBase64().data())


def loadUi(name):
    try:
        uiData, widgetType = uic.loadUiType(f"{Utils.joinPath(Config.UI_ROOT, name)}.ui")
    except:
        raise Exceptions.FileSystemError
    class UiWidget(uiData):
        def __init__(self):
            super(UiWidget, self).__init__()
            self.setupUi(self)
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            if widgetType == QtWidgets.QMainWindow or widgetType == QtWidgets.QDialog:
                self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
                self.setWindowIcon(QtGui.QIcon(Icons.APP_LOGO_ICON))
                self.setWindowTitle(self.windowTitle() or Config.APP_NAME)
            self.ignoreKeys = []
            self.setAds()

        def info(self, title, content, titleTranslate=True, contentTranslate=True, buttonText=None):
            Utils.info(title, content, titleTranslate, contentTranslate, buttonText, parent=self)

        def ask(self, title, content, titleTranslate=True, contentTranslate=True, okText=None, cancelText=None, defaultOk=False):
            return Utils.ask(title, content, titleTranslate, contentTranslate, okText, cancelText, defaultOk, parent=self)

        def setAds(self):
            adArea = self.findChildren(QtWidgets.QWidget, QtCore.QRegExp("^adArea_\d+$"))
            adGroup = self.findChildren(QtWidgets.QWidget, QtCore.QRegExp("^adGroup_\d+$"))
            if AdManager.Config.SHOW:
                for widget in adArea:
                    Utils.setPlaceholder(widget, AdManager.Ad(minimumSize=widget.minimumSize(), responsive=True, parent=self))
            else:
                for widget in adArea + adGroup:
                    widget.setParent(None)

        def ignoreKey(self, *args):
            for key in args:
                self.ignoreKeys.append(key)

        def keyPressEvent(self, event):
            if event.key() in self.ignoreKeys:
                event.ignore()
            self.keyPressEvent(event)
    return UiWidget


class UiFile:
    mainWindow = loadUi("mainWindow")
    loading = loadUi("loading")
    setup = loadUi("setup")
    settings = loadUi("settings")
    propertyView = loadUi("propertyView")
    account = loadUi("account")
    about = loadUi("about")
    documentView = loadUi("documentView")
    home = loadUi("home")
    search = loadUi("search")
    videoWidget = loadUi("videoWidget")
    videoDownloadWidget = loadUi("videoDownloadWidget")
    searchResult = loadUi("searchResult")
    downloadMenu = loadUi("downloadMenu")
    downloads = loadUi("downloads")
    downloadPreview = loadUi("downloadPreview")
    download = loadUi("download")


class Ui:
    MainWindow = None
    Loading = None
    Setup = None
    Settings = None
    PropertyView = None
    Account = None
    About = None
    DocumentView = None
    Home = None
    Search = None
    VideoWidget = None
    VideoDownloadWidget = None
    SearchResult = None
    DownloadMenu = None
    Downloads = None
    DownloadPreview = None
    Download = None


from Ui import MainWindow, Loading, Setup, Settings, PropertyView, Account, About, DocumentView, Home, Search, VideoWidget, VideoDownloadWidget, SearchResult, DownloadMenu, Downloads, DownloadPreview, Download


Ui.MainWindow = MainWindow.MainWindow
Ui.Loading = Loading.Loading
Ui.Setup = Setup.Setup
Ui.Settings = Settings.Settings
Ui.PropertyView = PropertyView.PropertyView
Ui.Account = Account.Account
Ui.About = About.About
Ui.DocumentView = DocumentView.DocumentView
Ui.Home = Home.Home
Ui.Search = Search.Search
Ui.VideoWidget = VideoWidget.VideoWidget
Ui.VideoDownloadWidget = VideoDownloadWidget.VideoDownloadWidget
Ui.SearchResult = SearchResult.SearchResult
Ui.DownloadMenu = DownloadMenu.DownloadMenu
Ui.Downloads = Downloads.Downloads
Ui.DownloadPreview = DownloadPreview.DownloadPreview
Ui.Download = Download.Download