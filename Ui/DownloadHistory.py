from Core.Ui import *
from Download.DownloadHistoryManager import DownloadHistoryManager


class PreviewWidgetItem(QtWidgets.QListWidgetItem):
    def __init__(self, downloadHistory, parent=None):
        super(PreviewWidgetItem, self).__init__(parent=parent)
        self.widget = Ui.DownloadHistoryView(downloadHistory, parent=parent)
        self.widget.setContentsMargins(10, 10, 10, 10)
        self.setSizeHint(self.widget.sizeHint())


class DownloadHistory(QtWidgets.QWidget, UiFile.downloadHistory):
    accountPageShowRequested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(DownloadHistory, self).__init__(parent=parent)
        self.previewItems = {}
        self.infoIcon = Utils.setSvgIcon(self.infoIcon, Icons.HISTORY_ICON)
        self.stackedWidget.setStyleSheet(f"#stackedWidget {{background-color: {self.stackedWidget.palette().color(QtGui.QPalette.Base).name()};}}")
        self.previewWidgetView.itemSelectionChanged.connect(self.previewWidgetView.clearSelection)
        self.previewWidgetView.itemClicked.connect(self.openFile)
        self.previewWidgetView.verticalScrollBar().setSingleStep(30)
        DownloadHistoryManager.historyCreated.connect(self.createHistoryView)
        DownloadHistoryManager.historyRemoved.connect(self.removeHistoryView)
        self.loadHistory()

    def loadHistory(self):
        for downloadHistory in DownloadHistoryManager.getHistoryList():
            self.createHistoryView(downloadHistory)

    def historyCountChanged(self):
        if len(self.previewItems) == 0:
            self.stackedWidget.setCurrentIndex(0)
        else:
            self.stackedWidget.setCurrentIndex(1)

    def createHistoryView(self, downloadHistory):
        item = PreviewWidgetItem(downloadHistory=downloadHistory)
        item.widget.accountPageShowRequested.connect(self.accountPageShowRequested)
        self.previewItems[downloadHistory] = item
        self.previewWidgetView.setMinimumWidth(item.sizeHint().width() + self.previewWidgetView.verticalScrollBar().sizeHint().width())
        self.previewWidgetView.insertItem(0, item)
        self.previewWidgetView.setItemWidget(item, item.widget)
        self.historyCountChanged()

    def removeHistoryView(self, downloadHistory):
        self.previewWidgetView.takeItem(self.previewWidgetView.row(self.previewItems.pop(downloadHistory)))
        self.historyCountChanged()

    def openFile(self, item):
        item.widget.openFileButton.click()