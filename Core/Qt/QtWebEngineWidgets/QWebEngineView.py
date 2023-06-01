from Services.Logging.ErrorDetector import ErrorDetector

from PyQt6 import QtCore, QtWebEngineCore, QtWebEngineWidgets


class Exceptions:
    class WebViewError(Exception):
        def __str__(self):
            return "Unable to load WebView."


class _QWebEngineView(QtWebEngineWidgets.QWebEngineView):
    firstLoad = True

    def __init__(self, parent=None):
        if ErrorDetector.hasHistory("WebView"):
            if ErrorDetector.getHistory("WebView") > ErrorDetector.MAX_IGNORE_COUNT:
                raise Exceptions.WebViewError
        self.detectorId = f"WebView_{self.__class__.__name__}_{id(self)}"
        ErrorDetector.setDetector(self.detectorId, 0)
        super(_QWebEngineView, self).__init__(parent=parent)
        ErrorDetector.setDetector(self.detectorId, 1)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.NoContextMenu)
        self._loading = False
        self.loadStarted.connect(self._onLoadStart)
        self.loadFinished.connect(self._onLoadFinish)
        if _QWebEngineView.firstLoad:
            QtWebEngineCore.QWebEngineProfile.setup()
            _QWebEngineView.firstLoad = False
        ErrorDetector.removeDetector(self.detectorId)

    def _onLoadStart(self):
        self._loading = True

    def _onLoadFinish(self):
        self._loading = False

    def isLoading(self):
        return self._loading

    def load(self, url):
        ErrorDetector.setDetector(self.detectorId, 2)
        super().load(url)
        ErrorDetector.removeDetector(self.detectorId)

    def dropEvent(self, event):
        event.ignore()
QtWebEngineWidgets.QWebEngineView = _QWebEngineView #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)