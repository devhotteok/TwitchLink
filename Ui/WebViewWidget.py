from Core.Ui import *

from PyQt6 import QtWebEngineCore

import typing


class WebViewWidget(QtWidgets.QWidget):
    iconChanged = QtCore.pyqtSignal(object, object)
    titleChanged = QtCore.pyqtSignal(object, str)
    tabCloseRequested = QtCore.pyqtSignal(object)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("webViewWidget", self)
        self._ui.webView = Utils.setPlaceholder(self._ui.webView, WebView(parent=self))
        self._ui.webView.urlChanged.connect(self.urlChangeHandler)
        self._ui.webView.iconChanged.connect(self.iconChangeHandler)
        self._ui.webView.titleChanged.connect(self.titleChangeHandler)
        self._ui.webView.loadStarted.connect(self.loadStarted)
        self._ui.webView.loadFinished.connect(self.loadFinished)
        self._ui.webView.tabCloseRequested.connect(self.tabCloseRequestHandler)
        self.newTabRequested = self._ui.webView.newTabRequested
        self._ui.backButton.clicked.connect(self._ui.webView.back)
        Utils.setIconViewer(self._ui.backButton, Icons.BACK)
        self._ui.forwardButton.clicked.connect(self._ui.webView.forward)
        Utils.setIconViewer(self._ui.forwardButton, Icons.FORWARD)
        self._ui.reloadButton.clicked.connect(self._ui.webView.reload)
        Utils.setIconViewer(self._ui.reloadButton, Icons.RELOAD)
        self._ui.stopLoadingButton.clicked.connect(self._ui.webView.stop)
        Utils.setIconViewer(self._ui.stopLoadingButton, Icons.CANCEL)
        self._ui.urlEdit.returnPressed.connect(self.urlEdited)
        self.reloadControlArea()
        self.reloadUrl()
        self._ui.infoIcon = Utils.setSvgIcon(self._ui.infoIcon, Icons.INFO)
        self._infoButtonIconViewer = Utils.setIconViewer(self._ui.infoButton, None)
        self.hideInfo()
        self.setupShortcuts()

    def setupShortcuts(self) -> None:
        self.backShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Back, self)
        self.backShortcut.activated.connect(self._ui.webView.back)
        self.forwardShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Forward, self)
        self.forwardShortcut.activated.connect(self._ui.webView.forward)
        self.refreshShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Refresh, self)
        self.refreshShortcut.activated.connect(self._ui.webView.reload)
        self.stopShortcut = QtGui.QShortcut(QtGui.QKeySequence.StandardKey.Cancel, self)
        self.stopShortcut.activated.connect(self._ui.webView.stop)
        self.devToolsShortcut = QtGui.QShortcut(QtGui.QKeySequence("F12"), self)
        self.devToolsShortcut.activated.connect(self._ui.webView.toggleDevTools)

    def setInspectedMode(self, page: QtWebEngineCore.QWebEnginePage) -> None:
        self.backShortcut.setEnabled(False)
        self.forwardShortcut.setEnabled(False)
        self.refreshShortcut.setEnabled(False)
        self.stopShortcut.setEnabled(False)
        self._ui.controlArea.hide()
        self.showInfo(f"{T('developer-tools')} - {T('#Close the window by pressing [{key}].', key='F12')}", icon=Icons.SETTINGS, buttonIcon=Icons.CLOSE, buttonTransparent=True, buttonHandler=self.hideInfo)
        self._ui.webView.page().setInspectedPage(page)

    def setProfile(self, profile: QtWebEngineCore.QWebEngineProfile) -> None:
        self._ui.webView.setProfile(profile)

    def reloadControlArea(self) -> None:
        isLoading = self._ui.webView.isLoading()
        self._ui.reloadButton.setVisible(not isLoading)
        self._ui.stopLoadingButton.setVisible(isLoading)
        self._ui.backButton.setEnabled(self._ui.webView.history().canGoBack())
        self._ui.forwardButton.setEnabled(self._ui.webView.history().canGoForward())

    def reloadUrl(self) -> None:
        self._ui.urlEdit.setText(self._ui.webView.url().toString())
        self._ui.urlEdit.clearFocus()

    def showInfo(self, text: str, icon: str | ThemedIcon | None = None, buttonIcon: QtGui.QIcon | ThemedIcon | None = None, buttonText: str = "", buttonTransparent: bool = False, buttonHandler: typing.Callable | None = None) -> None:
        self._ui.infoLabel.setText(text)
        if icon == None:
            self._ui.infoIcon.hide()
        else:
            self._ui.infoIcon.setIcon(icon)
            self._ui.infoIcon.show()
        try:
            self._ui.infoButton.clicked.disconnect()
        except:
            pass
        if buttonHandler == None:
            self._ui.infoButton.hide()
        else:
            self._infoButtonIconViewer.setIcon(buttonIcon)
            self._ui.infoButton.setText(buttonText)
            self._ui.infoButton.setStyleSheet("QPushButton {padding: 3px; background-color: transparent; border: 1px solid transparent; border-radius: 4px;} QPushButton:hover {background-color: rgba(255, 255, 255, 0.2); border: 1px solid #cccccc;} QPushButton:pressed {background-color: rgba(255, 255, 255, 0.35); border: 1px solid #aaaaaa;}" if buttonTransparent else "")
            self._ui.infoButton.clicked.connect(buttonHandler)
            self._ui.infoButton.show()
        self._ui.infoArea.show()

    def hideInfo(self) -> None:
        self._ui.infoArea.hide()

    def urlChangeHandler(self, url: QtCore.QUrl) -> None:
        self.reloadUrl()

    def iconChangeHandler(self, icon: QtGui.QIcon) -> None:
        self.iconChanged.emit(self, icon)

    def titleChangeHandler(self, title: str) -> None:
        self.setWindowTitle(title)
        self.titleChanged.emit(self, title)

    def urlEdited(self) -> None:
        self._ui.webView.setUrl(QtCore.QUrl.fromUserInput(self._ui.urlEdit.text()))
        self._ui.urlEdit.clearFocus()

    def loadStarted(self) -> None:
        self.reloadControlArea()
        self.reloadUrl()
        self._ui.urlEdit.clearFocus()
        self.iconChanged.emit(self, Icons.LOADING)

    def loadFinished(self, isSuccessful: bool) -> None:
        self.reloadControlArea()
        self.iconChanged.emit(self, self._ui.webView.icon() if isSuccessful else Icons.WEB)

    def tabCloseRequestHandler(self) -> None:
        self.tabCloseRequested.emit(self)


class WebView(QtWebEngineWidgets.QWebEngineView):
    newTabRequested = QtCore.pyqtSignal(WebViewWidget)
    tabCloseRequested = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.DefaultContextMenu)
        self._connectPageSignals()

    def setPage(self, page: QtWebEngineCore.QWebEnginePage) -> None:
        super().setPage(page)
        self._connectPageSignals()

    def _connectPageSignals(self) -> None:
        self.page().windowCloseRequested.connect(self.tabCloseRequested)

    def setProfile(self, profile: QtWebEngineCore.QWebEngineProfile) -> None:
        self.setPage(QtWebEngineCore.QWebEnginePage(profile, parent=self))

    def createWindow(self, type: QtWebEngineCore.QWebEnginePage.WebWindowType) -> QtWebEngineWidgets.QWebEngineView:
        webViewWidget = WebViewWidget()
        webViewWidget.setProfile(self.page().profile())
        self.newTabRequested.emit(webViewWidget)
        return webViewWidget._ui.webView

    def toggleDevTools(self) -> None:
        page = self.page().devToolsPage() if self.page().inspectedPage() == None else self.page()
        if page != None:
            page.windowCloseRequested.emit()
            return
        devToolsWidget = WebViewWidget()
        devToolsWidget.setProfile(self.page().profile())
        devToolsWidget.setInspectedMode(self.page())
        self.newTabRequested.emit(devToolsWidget)