from Core.GlobalExceptions import Exceptions
from Core.Config import Config
from Services.Utils.Utils import Utils
from Services.Translator.Translator import Translator, T
from Services.Ad import AdManager
from Database.Database import DB

from PyQt5 import QtCore, QtGui, QtWidgets, uic


class _QDialog(QtWidgets.QDialog):
    def exec(self):
        self.returnValue = False
        super().exec()
        return self.returnValue

    def accept(self, returnValue=True):
        self.returnValue = returnValue
        return super().accept()
QtWidgets.QDialog = _QDialog


class _QLabel(QtWidgets.QLabel):
    _keepImageRatio = False

    def setImageSizePolicy(self, minimumSize, maximumSize, keepImageRatio=True):
        self.setMinimumSize(*minimumSize)
        self.setMaximumSize(*maximumSize)
        self.keepImageRatio(keepImageRatio)

    def keepImageRatio(self, keepImageRatio):
        self._keepImageRatio = keepImageRatio

    def setText(self, text):
        return super().setText(str(text))

    def paintEvent(self, event):
        if self.pixmap() == None:
            if self.hasSelectedText():
                return super().paintEvent(event)
            else:
                painter = QtGui.QPainter(self)
                metrics = QtGui.QFontMetrics(self.font())
                elided = map(lambda text: metrics.elidedText(text, QtCore.Qt.ElideRight, self.width()), self.text().split("\n"))
                text = "\n".join(elided)
                painter.drawText(self.rect(), self.alignment(), text)
                self.setToolTip("" if text == self.text() else self.text())
        else:
            if self._keepImageRatio:
                margins = self.getContentsMargins()
                size = self.size() - QtCore.QSize(margins[0] + margins[2], margins[1] + margins[3])
                painter = QtGui.QPainter(self)
                point = QtCore.QPoint(0, 0)
                scaledPix = self.pixmap().scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                point.setX((size.width() - scaledPix.width()) / 2 + margins[0])
                point.setY((size.height() - scaledPix.height()) / 2 + margins[1])
                painter.drawPixmap(point, scaledPix)
            else:
                return super().paintEvent(event)
QtWidgets.QLabel = _QLabel


class _QSpinBox(QtWidgets.QSpinBox):
    def setValueSilent(self, value):
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)
QtWidgets.QSpinBox = _QSpinBox


def loadUi(ui_name):
    try:
        UiClass = uic.loadUiType("{}.ui".format(Utils.joinPath(Config.UI_ROOT, ui_name)))[0]
    except:
        raise Exceptions.FileSystemError
    class UiManager(UiClass):
        def __init__(self, useWindowGeometry=True):
            self.useWindowGeometry = useWindowGeometry
            self.setupUi(self)
            self.setupUiLayout()
            self.ignoreKeys = []

        def setupUiLayout(self):
            if isinstance(self, QtWidgets.QMainWindow) or isinstance(self, QtWidgets.QDialog):
                self.setWindowIcon(QtGui.QIcon(Config.ICON_IMAGE))
                title = self.windowTitle()
                if title == "":
                    self.setWindowTitle(Config.APP_NAME)
                else:
                    self.setWindowTitle("{} - {}".format(Config.APP_NAME, T(title)))
                self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
                if self.useWindowGeometry:
                    windowGeometry = DB.temp.getWindowGeometry(self.__class__.__name__)
                    if windowGeometry != None:
                        self.restoreGeometry(QtCore.QByteArray.fromBase64(windowGeometry))
            self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
            self.setAds()
            self.setFont(Translator.getFont())
            for widget in self.findChildren(QtWidgets.QTextBrowser):
                widget.setFont(Translator.getDocFont(widget.font()))
            for widget in self.findChildren(QtWidgets.QLabel):
                widget.setFont(Translator.getFont(widget.font()))

        def setAds(self):
            adArea = self.findChildren(QtWidgets.QWidget, QtCore.QRegExp("^adArea_\d+$"))
            adGroup = self.findChildren(QtWidgets.QWidget, QtCore.QRegExp("^adGroup_\d+$"))
            if AdManager.Config.SHOW:
                for widget in adArea:
                    Utils.setPlaceholder(widget, AdManager.Ad(minimumSize=widget.minimumSize(), responsive=True))
            else:
                for widget in adArea + adGroup:
                    widget.setParent(None)

        def ignoreKey(self, *args):
            for key in args:
                self.ignoreKeys.append(key)

        def keyPressEvent(self, event):
            if event.key() in self.ignoreKeys:
                return event.ignore()
            else:
                return self.keyPressEvent(event)

        def done(self, *args, **kwargs):
            self.saveWindow()
            return self.done(*args, **kwargs)

        def saveWindow(self):
            if self.useWindowGeometry:
                DB.temp.setWindowGeometry(self.__class__.__name__, self.saveGeometry().toBase64().data())
    return UiManager


class UiFile:
    mainWindow = loadUi("mainWindow")
    loading = loadUi("loading")
    settings = loadUi("settings")
    formInfo = loadUi("formInfo")
    account = loadUi("account")
    about = loadUi("about")
    termsOfService = loadUi("termsOfService")
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
    Settings = None
    FormInfo = None
    Account = None
    About = None
    TermsOfService = None
    Home = None
    Search = None
    VideoWidget = None
    VideoDownloadWidget = None
    SearchResult = None
    DownloadMenu = None
    Downloads = None
    DownloadPreview = None
    Download = None


from Ui import MainWindow, Loading, Settings, FormInfo, Account, About, TermsOfService, Home, Search, VideoWidget, VideoDownloadWidget, SearchResult, DownloadMenu, Downloads, DownloadPreview, Download


Ui.MainWindow = MainWindow.MainWindow
Ui.Loading = Loading.Loading
Ui.Settings = Settings.Settings
Ui.FormInfo = FormInfo.FormInfo
Ui.Account = Account.Account
Ui.About = About.About
Ui.TermsOfService = TermsOfService.TermsOfService
Ui.Home = Home.Home
Ui.Search = Search.Search
Ui.VideoWidget = VideoWidget.VideoWidget
Ui.VideoDownloadWidget = VideoDownloadWidget.VideoDownloadWidget
Ui.SearchResult = SearchResult.SearchResult
Ui.DownloadMenu = DownloadMenu.DownloadMenu
Ui.Downloads = Downloads.Downloads
Ui.DownloadPreview = DownloadPreview.DownloadPreview
Ui.Download = Download.Download