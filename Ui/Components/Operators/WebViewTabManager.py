from Core.Ui import *
from Ui.Components.Operators.TabManager import TabManager


class WebViewTabManager(TabManager):
    def __init__(self, parent=None):
        super(WebViewTabManager, self).__init__(parent=parent)
        self.webViewWidgets = []

    def updateWebTabIcon(self, widget, icon):
        self.setTabIcon(self.indexOf(widget), self.getDefaultIcon(widget.webView, widget.webView.url().toString()) if icon.isNull() else icon)

    def updateWebTabTitle(self, widget, title):
        self.setTabText(self.indexOf(widget), title)

    def getDefaultIcon(self, webView, url):
        if url.startswith("file:///"):
            return Icons.FOLDER_ICON
        elif url.startswith("devtools://"):
            if webView.page().inspectedPage() != None:
                return Icons.SETTINGS_ICON
        return Icons.WEB_ICON

    def addWebTab(self, webViewWidget, index=-1, closable=True, uniqueValue=None):
        webViewWidget.iconChanged.connect(self.updateWebTabIcon)
        webViewWidget.titleChanged.connect(self.updateWebTabTitle)
        webViewWidget.newTabRequested.connect(self.openWebTab)
        webViewWidget.tabCloseRequested.connect(self.closeWebTab)
        self.webViewWidgets.append(webViewWidget)
        return self.addTab(webViewWidget, index=index, closable=closable, uniqueValue=uniqueValue)

    def openWebTab(self, webViewWidget, index=-1, closable=True, uniqueValue=None):
        self.setCurrentIndex(self.addWebTab(webViewWidget, index=index, closable=closable, uniqueValue=uniqueValue))

    def closeWebTab(self, webViewWidget):
        self.closeTab(self.indexOf(webViewWidget))

    def closeAllWebTabs(self):
        while len(self.webViewWidgets) != 0:
            super().closeTab(self.indexOf(self.webViewWidgets.pop(0)))

    def closeTab(self, index):
        widget = self.widget(index)
        if widget in self.webViewWidgets:
            self.webViewWidgets.remove(widget)
            devToolsPage = widget.webView.page().devToolsPage()
            if devToolsPage != None:
                devToolsPage.windowCloseRequested.emit()
        super().closeTab(index)