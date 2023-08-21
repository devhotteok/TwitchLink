from Core import App
from Core.App import T
from Core.GlobalExceptions import Exceptions
from Core.Config import Config
from Services.Utils.Utils import Utils
from Services.Image.Presets import *
from Services import PartnerContent

from PyQt6 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets, uic

import typing


class WindowGeometryManager:
    def __init__(self):
        super().__init__()
        self.setWindowGeometryKey()

    def setWindowGeometryKey(self, key: str | None = None) -> None:
        self._windowGeometryKey = key or self.__class__.__name__

    def getWindowGeometryKey(self) -> str:
        return self._windowGeometryKey

    def loadWindowGeometry(self) -> None:
        if App.Preferences.temp.hasWindowGeometry(self._windowGeometryKey):
            self.restoreGeometry(QtCore.QByteArray.fromBase64(App.Preferences.temp.getWindowGeometry(self._windowGeometryKey)))

    def saveWindowGeometry(self) -> None:
        App.Preferences.temp.setWindowGeometry(self._windowGeometryKey, self.saveGeometry().toBase64().data())


class UiLoader:
    cache = {}

    @classmethod
    def load(cls, name: str, instance: QtWidgets.QWidget) -> typing.Any:
        if name not in cls.cache:
            try:
                cls.cache[name] = uic.loadUiType(f"{Utils.joinPath(Config.UI_ROOT, name)}.ui")[0]
            except:
                raise Exceptions.FileSystemError
        GeneratedClass = cls.cache[name]
        widget = GeneratedClass()
        widget.setupUi(instance)
        cls.setupInstance(instance)
        return widget

    @classmethod
    def setupInstance(cls, instance: QtWidgets.QWidget) -> None:
        instance.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        if isinstance(instance, QtWidgets.QMainWindow) or isinstance(instance, QtWidgets.QDialog):
            instance.setWindowFlag(QtCore.Qt.WindowType.WindowContextHelpButtonHint, False)
            instance.setWindowIcon(QtGui.QIcon(Icons.APP_LOGO_ICON))
            instance.setWindowTitle(instance.windowTitle() or Config.APP_NAME)
        cls.setPartnerContent(instance)

    @staticmethod
    def setPartnerContent(target: QtWidgets.QWidget) -> None:
        partnerContentArea = [widget for widget in target.findChildren(QtWidgets.QWidget, QtCore.QRegularExpression("^partnerContentArea_\d+$")) if isinstance(widget, QtWidgets.QWidget)]
        partnerContentGroup = [widget for widget in target.findChildren(QtWidgets.QWidget, QtCore.QRegularExpression("^partnerContentGroup_\d+$")) if isinstance(widget, QtWidgets.QWidget)]
        if PartnerContent.Config.ENABLED:
            for widget in partnerContentArea:
                Utils.setPlaceholder(widget, PartnerContent.PartnerContentWidget(contentId=f"{target.__class__.__name__}.{widget.objectName()}", contentSize=widget.minimumSize(), responsive=True, parent=target))
        else:
            for widget in partnerContentArea + partnerContentGroup:
                widget.setParent(None)
                widget.deleteLater()


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
    DownloadViewControlBar = None
    DownloadInfoView = None
    DownloaderView = None
    Downloads = None
    DownloadPreview = None
    Download = None
    ScheduledDownloads = None
    ScheduledDownloadPreview = None
    ScheduledDownloadSettings = None
    DownloadHistories = None
    DownloadHistoryView = None
    WebViewWidget = None


from Ui import MainWindow, Loading, Setup, Settings, PropertyView, Account, About, DocumentView, Home, Search, VideoWidget, VideoDownloadWidget, SearchResult, DownloadMenu, DownloadViewControlBar, DownloadInfoView, DownloaderView, Downloads, DownloadPreview, Download, ScheduledDownloads, ScheduledDownloadPreview, ScheduledDownloadSettings, DownloadHistories, DownloadHistoryView, WebViewWidget


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
Ui.DownloadViewControlBar = DownloadViewControlBar.DownloadViewControlBar
Ui.DownloadInfoView = DownloadInfoView.DownloadInfoView
Ui.DownloaderView = DownloaderView.DownloaderView
Ui.Downloads = Downloads.Downloads
Ui.DownloadPreview = DownloadPreview.DownloadPreview
Ui.Download = Download.Download
Ui.ScheduledDownloads = ScheduledDownloads.ScheduledDownloads
Ui.ScheduledDownloadPreview = ScheduledDownloadPreview.ScheduledDownloadPreview
Ui.ScheduledDownloadSettings = ScheduledDownloadSettings.ScheduledDownloadSettings
Ui.DownloadHistories = DownloadHistories.DownloadHistories
Ui.DownloadHistoryView = DownloadHistoryView.DownloadHistoryView
Ui.WebViewWidget = WebViewWidget.WebViewWidget