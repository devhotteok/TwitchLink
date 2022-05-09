from .Config import Config

from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets


class Ad(QtWidgets.QWidget):
    def __init__(self, minimumSize, responsive=False, parent=None):
        super(Ad, self).__init__(parent=parent)
        self.adView = AdView(parent=self)
        self.setLayout(QtWidgets.QHBoxLayout(self))
        self.layout().addChildWidget(self.adView)
        if responsive:
            self.setMinimumSize(minimumSize)
        else:
            self.setFixedSize(minimumSize)
        self.adView.getAd(minimumSize.width(), minimumSize.height())

    def setContentsMargins(self, left, top, right, bottom):
        self.adView.setContentsMargins(left, top, right, bottom)

    def minimumSizeHint(self):
        return self.minimumSize()

    def sizeHint(self):
        return self.minimumSizeHint()

    def resizeEvent(self, event):
        self.adView.resize(self.size())
        super().resizeEvent(event)


class AdView(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent=None):
        super(AdView, self).__init__(parent=parent)
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setPage(AdPage(parent=self))
        self.currentAd = None
        self.hide()
        self.loadFinished.connect(self.showAd)

    def getAvailableAds(self, width, height):
        availableAds = []
        for adSize in Config.SIZE_LIST:
            if adSize[0] > width or adSize[1] > height:
                continue
            availableAds.append(adSize)
        return availableAds

    def getAd(self, width, height):
        availableAds = self.getAvailableAds(width, height)
        if len(availableAds) == 0:
            if self.currentAd != None:
                self.currentAd = None
                self.removeAd()
        else:
            if self.currentAd != availableAds[0]:
                self.currentAd = availableAds[0]
                self.loadAd(self.currentAd)

    def removeAd(self):
        self.stop()
        self.hide()

    def loadAd(self, size):
        self.removeAd()
        self.load(QtCore.QUrl(f"{Config.SERVER}?{Config.URL_QUERY.format(width=size[0], height=size[1])}"))

    def showAd(self, success):
        if success:
            self.show()


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