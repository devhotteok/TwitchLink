from .Config import Config

from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets


class AdView(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent=None):
        super(AdView, self).__init__(parent=parent)
        self.adSize = (0, 0)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setPage(AdPage(parent=self))

    def moveTo(self, widget):
        if self.parent() != None:
            self.parent().destroyed.disconnect(self.parentDestroyed)
        widget.layout().addWidget(self)
        widget.destroyed.connect(self.parentDestroyed)
        if widget.responsive:
            self.setMinimumSize(0, 0)
            self.setMaximumSize(QtWidgets.QWIDGETSIZE_MAX, QtWidgets.QWIDGETSIZE_MAX)
        else:
            self.setFixedSize(*self.adSize)

    def parentDestroyed(self):
        self.setParent(None)

    def getAd(self, width, height):
        for adSize in Config.SIZE_LIST:
            if adSize[0] > width or adSize[1] > height:
                continue
            self.loadAd(adSize)
            return

    def loadAd(self, size):
        self.adSize = size
        self.load(QtCore.QUrl(f"{Config.SERVER}?{Config.URL_QUERY.format(width=size[0], height=size[1])}"))


class AdPage(QtWebEngineWidgets.QWebEnginePage):
    def __init__(self, parent=None):
        super(AdPage, self).__init__(parent=parent)
        settings = self.settings()
        settings.setAttribute(QtWebEngineWidgets.QWebEngineSettings.ShowScrollBars, False)
        settings.setAttribute(QtWebEngineWidgets.QWebEngineSettings.ErrorPageEnabled, False)
        self.setBackgroundColor(QtCore.Qt.transparent)
        self.loadFinished.connect(self.setup)

    def setup(self, success):
        if success:
            self.runJavaScript("document.body.style.webkitUserSelect='none';document.body.style.webkitUserDrag='none';")

    def createWindow(self, type):
        return PageClickHandler(parent=self)


class PageClickHandler(QtWebEngineWidgets.QWebEnginePage):
    def __init__(self, parent=None):
        super(PageClickHandler, self).__init__(parent=parent)
        self.urlChanged.connect(self.urlChangeHandler)

    def urlChangeHandler(self, url):
        QtGui.QDesktopServices.openUrl(url)
        self.deleteLater()