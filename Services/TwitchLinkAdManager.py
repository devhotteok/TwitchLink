from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QDesktopServices
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage

from TwitchLinkConfig import Config


class AdManager(QWidget):
    def __init__(self, width, height):
        super().__init__()
        if Config.SHOW_ADS:
            layout = QVBoxLayout(self)
            layout.setAlignment(Qt.AlignCenter)
            layout.setContentsMargins(0, 0, 0, 0)
            self.webEngine = QWebEngineView()
            self.webEngine.setPage(Page(self.webEngine))
            self.webEngine.load(QUrl("{}?width={}&height={}".format(Config.AD_SERVER, width, height)))
            self.webEngine.setContextMenuPolicy(Qt.NoContextMenu)
            self.webEngine.setFixedSize(width, height)
            sizePolicy = QSizePolicy()
            sizePolicy.setRetainSizeWhenHidden(True)
            self.webEngine.setSizePolicy(sizePolicy)
            self.webEngine.hide()
            self.webEngine.loadFinished.connect(self.showAd)
            layout.addWidget(self.webEngine)

    def showAd(self):
        self.webEngine.show()

class Page(QWebEnginePage):
    def createWindow(self, type):
        page = Page(self)
        page.urlChanged.connect(self.on_url_changed)
        return page

    def on_url_changed(self, url):
        self.sender().deleteLater()
        QDesktopServices.openUrl(url)