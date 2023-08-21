from .PartnerContentWidget import PartnerContentWidget
from .Config import Config

from PyQt6 import QtCore, QtGui, QtWidgets, QtWebEngineCore, QtWebEngineWidgets


class PartnerContentView(QtWebEngineWidgets.QWebEngineView):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.contentSize = (0, 0)
        self.setPage(PartnerContentPage(parent=self))
        self.loadFinished.connect(self._setup)
        self.hide()

    def moveTo(self, widget: PartnerContentWidget) -> None:
        if self.parent() != None:
            self.parent().destroyed.disconnect(self._parentDestroyed)
        widget.layout().addWidget(self)
        widget.destroyed.connect(self._parentDestroyed)
        if widget.responsive:
            self.setMinimumSize(0, 0)
            self.setMaximumSize(QtWidgets.QWIDGETSIZE_MAX, QtWidgets.QWIDGETSIZE_MAX)
        else:
            self.setFixedSize(*self.contentSize)

    def _parentDestroyed(self) -> None:
        self.setParent(None)

    def getContent(self, width: int, height: int) -> None:
        for contentSize in Config.SIZE_LIST:
            if contentSize[0] > width or contentSize[1] > height:
                continue
            self.loadContent(contentSize)
            return

    def loadContent(self, size: tuple[int, int]) -> None:
        self.contentSize = size
        self.load(QtCore.QUrl(f"{Config.SERVER}?{Config.URL_QUERY.format(width=size[0], height=size[1])}"))

    def _setup(self, success: bool) -> None:
        if success:
            self.show()


class PartnerContentPage(QtWebEngineCore.QWebEnginePage):
    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.setBackgroundColor(QtGui.QColor(255, 255, 255, 0))
        self.loadFinished.connect(self._setup)

    def _setup(self, success: bool) -> None:
        if success:
            self.runJavaScript("document.body.style.webkitUserSelect='none';document.body.style.webkitUserDrag='none';")

    def createWindow(self, type: QtWebEngineCore.QWebEnginePage.WebWindowType) -> QtWebEngineCore.QWebEnginePage:
        return PageClickHandler(parent=self)


class PageClickHandler(QtWebEngineCore.QWebEnginePage):
    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.urlChanged.connect(self._urlChangeHandler)

    def _urlChangeHandler(self, url: QtCore.QUrl) -> None:
        QtGui.QDesktopServices.openUrl(url)
        self.deleteLater()