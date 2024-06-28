from Core.Ui import *
from Services.PartnerContent.PartnerContentInFeedWidgetListViewer import PartnerContentInFeedWidgetListViewer
from Download.History.DownloadHistory import DownloadHistory


class DownloadHistories(QtWidgets.QWidget):
    accountPageShowRequested = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.previewWidgets = {}
        self._ui = UiLoader.load("downloadHistories", self)
        App.ThemeManager.themeUpdated.connect(self._setupThemeStyle)
        self._setupThemeStyle()
        self._ui.infoIcon = Utils.setSvgIcon(self._ui.infoIcon, Icons.HISTORY)
        self._widgetListViewer = PartnerContentInFeedWidgetListViewer(self._ui.previewWidgetView, partnerContentSize=QtCore.QSize(320, 100), parent=self)
        self._widgetListViewer.widgetClicked.connect(self.openFile)
        App.DownloadHistory.historyCreated.connect(self.createHistoryView)
        App.DownloadHistory.historyRemoved.connect(self.removeHistoryView)
        self.loadHistory()

    def _setupThemeStyle(self) -> None:
        self._ui.stackedWidget.setStyleSheet(f"#stackedWidget {{background-color: {App.Instance.palette().color(QtGui.QPalette.ColorGroup.Normal, QtGui.QPalette.ColorRole.Base).name()};}}")

    def loadHistory(self) -> None:
        self._widgetListViewer.setAutoReloadEnabled(False)
        for downloadHistory in App.DownloadHistory.getHistoryList():
            self.createHistoryView(downloadHistory)
        self._widgetListViewer.setAutoReloadEnabled(True)

    def historyCountChanged(self) -> None:
        self._ui.stackedWidget.setCurrentIndex(0 if len(self.previewWidgets) == 0 else 1)

    def createHistoryView(self, downloadHistory: DownloadHistory) -> None:
        widget = Ui.DownloadHistoryView(downloadHistory, parent=None)
        widget.accountPageShowRequested.connect(self.accountPageShowRequested)
        self._widgetListViewer.insertWidget(0, widget)
        self.previewWidgets[downloadHistory] = widget
        self.historyCountChanged()

    def removeHistoryView(self, downloadHistory: DownloadHistory) -> None:
        self._widgetListViewer.removeWidget(self.previewWidgets.pop(downloadHistory))
        self.historyCountChanged()

    def openFile(self, widget: Ui.DownloadHistoryView) -> None:
        widget.clickHandler()