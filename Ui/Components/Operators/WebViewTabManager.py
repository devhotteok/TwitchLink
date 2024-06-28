from Core.Ui import *
from Ui.Components.Operators.TabManager import TabManager


class WebViewTabManager(TabManager):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.webViewWidgets = []

    def updateWebTabIcon(self, widget: Ui.WebViewWidget, icon: QtGui.QIcon | ThemedIcon) -> None:
        if isinstance(icon, QtGui.QIcon) and icon.isNull():
            tabIcon = self.getDefaultIcon(widget._ui.webView, widget._ui.webView.url())
        else:
            tabIcon = icon
        self.setTabIcon(self.indexOf(widget), tabIcon)

    def updateWebTabTitle(self, widget: Ui.WebViewWidget, title: str) -> None:
        self.setTabText(self.indexOf(widget), title)

    def getDefaultIcon(self, webView: QtWebEngineWidgets.QWebEngineView, url: QtCore.QUrl) -> ThemedIcon:
        if url.toString().startswith("file:///"):
            return Icons.FOLDER
        elif url.toString().startswith("devtools://"):
            if webView.page().inspectedPage() != None:
                return Icons.SETTINGS
        return Icons.WEB

    def addWebTab(self, webViewWidget: Ui.WebViewWidget, index: int = -1, closable: bool = True, uniqueValue: typing.Any = None) -> int:
        webViewWidget.iconChanged.connect(self.updateWebTabIcon)
        webViewWidget.titleChanged.connect(self.updateWebTabTitle)
        webViewWidget.newTabRequested.connect(self.openWebTab)
        webViewWidget.tabCloseRequested.connect(self.closeWebTab)
        self.webViewWidgets.append(webViewWidget)
        return self.addTab(webViewWidget, index=index, closable=closable, uniqueValue=uniqueValue)

    def openWebTab(self, webViewWidget: Ui.WebViewWidget, index: int = -1, closable: bool = True, uniqueValue: typing.Any = None) -> None:
        self.setCurrentIndex(self.addWebTab(webViewWidget, index=index, closable=closable, uniqueValue=uniqueValue))

    def closeWebTab(self, webViewWidget: Ui.WebViewWidget) -> None:
        self.closeTab(self.indexOf(webViewWidget))

    def closeAllWebTabs(self) -> None:
        while len(self.webViewWidgets) != 0:
            self.closeTab(self.indexOf(self.webViewWidgets[0]))

    def closeTab(self, index: int) -> None:
        widget = self.widget(index)
        if widget in self.webViewWidgets:
            devToolsPage = widget._ui.webView.page().devToolsPage()
            if devToolsPage != None:
                devToolsPage.windowCloseRequested.emit()
            self.webViewWidgets.remove(widget)
        super().closeTab(index)