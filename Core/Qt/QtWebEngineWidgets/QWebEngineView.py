from PyQt6 import QtCore, QtGui, QtWebEngineCore, QtWebEngineWidgets

import os


os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = "--enable-experimental-web-platform-features"


class _QWebEngineView(QtWebEngineWidgets.QWebEngineView):
    firstLoad = True

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        self._loading = False
        self.loadStarted.connect(self._onLoadStart)
        self.loadFinished.connect(self._onLoadFinish)
        if _QWebEngineView.firstLoad:
            QtWebEngineCore.QWebEngineProfile.setup()
            _QWebEngineView.firstLoad = False

    def _onLoadStart(self) -> None:
        self._loading = True

    def _onLoadFinish(self) -> None:
        self._loading = False

    def isLoading(self) -> bool:
        return self._loading

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        event.ignore()
QtWebEngineWidgets.QWebEngineView = _QWebEngineView #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)