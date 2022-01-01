from .Config import Config

from PyQt5 import QtCore, QtGui, QtWidgets, QtWebEngineWidgets


class Ad(QtWidgets.QWidget):
    def __init__(self, minimumSize, responsive=False):
        super().__init__()
        self.adView = AdView()
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().addChildWidget(self.adView)
        if responsive:
            self.setMinimumSize(minimumSize)
        else:
            self.setFixedSize(minimumSize)
        self.adView.getAd(minimumSize.width(), minimumSize.height())

    def resizeEvent(self, event):
        self.adView.resize(self.size())
        return super().resizeEvent(event)


class AdView(QtWebEngineWidgets.QWebEngineView):
    def __init__(self):
        super().__init__()
        self.currentAd = None
        self.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Ignored)
        self.setContextMenuPolicy(QtCore.Qt.NoContextMenu)
        self.setPage(Page(self))
        self.loadFinished.connect(self.showAd)
        self.hide()

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
        self.load(QtCore.QUrl("{}?{}".format(Config.SERVER, Config.URL_QUERY.format(width=size[0], height=size[1]))))

    def showAd(self, success):
        if success:
            self.page().runJavaScript("document.body.style.webkitUserSelect = 'none';document.body.style.webkitUserDrag = 'none';")
            self.show()
        else:
            self.hide()

    def dropEvent(self, event):
        return event.ignore()


class Page(QtWebEngineWidgets.QWebEnginePage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        settings = self.settings()
        settings.setAttribute(QtWebEngineWidgets.QWebEngineSettings.ShowScrollBars, False)
        settings.setAttribute(QtWebEngineWidgets.QWebEngineSettings.ErrorPageEnabled, False)
        self.setBackgroundColor(QtCore.Qt.transparent)

    def createWindow(self, type):
        page = Page(self)
        page.urlChanged.connect(self.on_url_changed)
        return page

    def on_url_changed(self, url):
        self.sender().deleteLater()
        QtGui.QDesktopServices.openUrl(url)