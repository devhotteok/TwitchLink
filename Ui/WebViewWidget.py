from Core.Ui import *


class WebViewWidget(QtWidgets.QWidget, UiFile.webViewWidget):
    iconChanged = QtCore.pyqtSignal(object, QtGui.QIcon)
    titleChanged = QtCore.pyqtSignal(object, str)
    tabCloseRequested = QtCore.pyqtSignal(object)

    DEFAULT_LOADING_ICON = QtGui.QIcon(Icons.LOADING_ICON)
    DEFAULT_FAILED_ICON = QtGui.QIcon(Icons.WEB_ICON)

    def __init__(self, parent=None):
        super(WebViewWidget, self).__init__(parent=parent)
        self.webView = Utils.setPlaceholder(self.webView, WebView(parent=self))
        self.webView.urlChanged.connect(self.urlChangeHandler)
        self.webView.iconChanged.connect(self.iconChangeHandler)
        self.webView.titleChanged.connect(self.titleChangeHandler)
        self.webView.loadStarted.connect(self.loadStarted)
        self.webView.loadFinished.connect(self.loadFinished)
        self.webView.tabCloseRequested.connect(self.tabCloseRequestHandler)
        self.newTabRequested = self.webView.newTabRequested
        self.backButton.clicked.connect(self.webView.back)
        self.forwardButton.clicked.connect(self.webView.forward)
        self.reloadButton.clicked.connect(self.webView.reload)
        self.stopLoadingButton.clicked.connect(self.webView.stop)
        self.urlEdit.returnPressed.connect(self.urlEdited)
        self.reloadControlArea()
        self.reloadUrl()
        self.infoIcon = Utils.setSvgIcon(self.infoIcon, Icons.INFO_ICON)
        self.hideInfo()
        self.setupShortcuts()

    def setupShortcuts(self):
        self.backShortcut = QtWidgets.QShortcut(QtGui.QKeySequence.Back, self)
        self.backShortcut.activated.connect(self.webView.back)
        self.forwardShortcut = QtWidgets.QShortcut(QtGui.QKeySequence.Forward, self)
        self.forwardShortcut.activated.connect(self.webView.forward)
        self.refreshShortcut = QtWidgets.QShortcut(QtGui.QKeySequence.Refresh, self)
        self.refreshShortcut.activated.connect(self.webView.reload)
        self.stopShortcut = QtWidgets.QShortcut(QtGui.QKeySequence.Cancel, self)
        self.stopShortcut.activated.connect(self.webView.stop)
        self.devToolsShortcut = QtWidgets.QShortcut(QtGui.QKeySequence("F12"), self)
        self.devToolsShortcut.activated.connect(self.webView.toggleDevTools)

    def setInspectedMode(self, page):
        self.backShortcut.setEnabled(False)
        self.forwardShortcut.setEnabled(False)
        self.refreshShortcut.setEnabled(False)
        self.stopShortcut.setEnabled(False)
        self.controlArea.hide()
        self.showInfo(f"{T('developer-tools')} - {T('#Close the window by pressing [{key}].', key='F12')}", icon=Icons.SETTINGS_ICON, buttonIcon=Icons.CLOSE_ICON, buttonTransparent=True, buttonHandler=self.hideInfo)
        self.webView.page().setInspectedPage(page)

    def setProfile(self, profile):
        self.webView.setProfile(profile)

    def reloadControlArea(self):
        isLoading = self.webView.isLoading()
        self.reloadButton.setVisible(not isLoading)
        self.stopLoadingButton.setVisible(isLoading)
        self.backButton.setEnabled(self.webView.history().canGoBack())
        self.forwardButton.setEnabled(self.webView.history().canGoForward())

    def reloadUrl(self):
        self.urlEdit.setText(self.webView.url().toString())
        self.urlEdit.clearFocus()

    def showInfo(self, text, icon=None, buttonIcon=None, buttonText="", buttonTransparent=False, buttonHandler=None):
        self.infoLabel.setText(text)
        if icon == None:
            self.infoIcon.hide()
        else:
            self.infoIcon.load(icon)
            self.infoIcon.show()
        try:
            self.infoButton.clicked.disconnect()
        except:
            pass
        if buttonHandler == None:
            self.infoButton.hide()
        else:
            self.infoButton.setIcon(QtGui.QIcon(buttonIcon))
            self.infoButton.setText(buttonText)
            self.infoButton.setStyleSheet("QPushButton:!hover {background-color: transparent;}" if buttonTransparent else "")
            self.infoButton.clicked.connect(buttonHandler)
            self.infoButton.show()
        self.infoArea.show()

    def hideInfo(self):
        self.infoArea.hide()

    def urlChangeHandler(self, url):
        self.reloadUrl()

    def iconChangeHandler(self, icon):
        self.iconChanged.emit(self, icon)

    def titleChangeHandler(self, title):
        self.setWindowTitle(title)
        self.titleChanged.emit(self, title)

    def urlEdited(self):
        self.webView.setUrl(QtCore.QUrl.fromUserInput(self.urlEdit.text()))
        self.urlEdit.clearFocus()

    def loadStarted(self):
        self.reloadControlArea()
        self.reloadUrl()
        self.urlEdit.clearFocus()
        self.iconChanged.emit(self, self.DEFAULT_LOADING_ICON)

    def loadFinished(self, result):
        self.reloadControlArea()
        self.iconChanged.emit(self, self.webView.icon() if result else self.DEFAULT_FAILED_ICON)

    def tabCloseRequestHandler(self):
        self.tabCloseRequested.emit(self)


class WebView(QtWebEngineWidgets.QWebEngineView):
    newTabRequested = QtCore.pyqtSignal(object)
    tabCloseRequested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(WebView, self).__init__(parent=parent)
        self.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self._connectPageSignals()

    def setPage(self, page):
        super().setPage(page)
        self._connectPageSignals()

    def _connectPageSignals(self):
        self.page().windowCloseRequested.connect(self.tabCloseRequested)

    def setProfile(self, profile):
        self.setPage(QtWebEngineWidgets.QWebEnginePage(profile, self))

    def createWindow(self, type):
        webViewWidget = WebViewWidget()
        webViewWidget.setProfile(self.page().profile())
        self.newTabRequested.emit(webViewWidget)
        return webViewWidget.webView

    def toggleDevTools(self):
        page = self.page().devToolsPage() if self.page().inspectedPage() == None else self.page()
        if page != None:
            page.windowCloseRequested.emit()
            return
        devToolsWidget = WebViewWidget()
        devToolsWidget.setProfile(self.page().profile())
        devToolsWidget.setInspectedMode(self.page())
        self.newTabRequested.emit(devToolsWidget)