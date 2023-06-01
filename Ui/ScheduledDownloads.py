from Core.Ui import *
from Services.Messages import Messages
from Download.ScheduledDownloadManager import ScheduledDownloadManager


class PreviewWidgetItem(QtWidgets.QListWidgetItem):
    def __init__(self, scheduledDownloadId, parent=None):
        super(PreviewWidgetItem, self).__init__(parent=parent)
        self.widget = Ui.ScheduledDownloadPreview(scheduledDownloadId, parent=parent)
        self.widget.setContentsMargins(10, 10, 10, 10)
        self.widget.resizedSignal.connect(self.resize, QtCore.Qt.ConnectionType.QueuedConnection)
        self.resize()

    def resize(self):
        self.setSizeHint(self.widget.sizeHint())


class ScheduledDownloads(QtWidgets.QWidget, UiFile.scheduledDownloads):
    def __init__(self, parent=None):
        super(ScheduledDownloads, self).__init__(parent=parent)
        self.previewItems = {}
        self.showEnableState()
        self.enableButton.clicked.connect(self.enableButtonClicked)
        self.infoIcon = Utils.setSvgIcon(self.infoIcon, Icons.SCHEDULED_ICON)
        self.stackedWidget.setStyleSheet(f"#stackedWidget {{background-color: {self.stackedWidget.palette().color(QtGui.QPalette.ColorGroup.Normal, QtGui.QPalette.ColorRole.Base).name()};}}")
        self.previewWidgetView.itemSelectionChanged.connect(self.previewWidgetView.clearSelection)
        self.showStats()
        self.addScheduledDownloadButton.clicked.connect(self.addScheduledDownload)
        ScheduledDownloadManager.enabledChangedSignal.connect(self.showEnableState)
        ScheduledDownloadManager.createdSignal.connect(self.scheduledDownloadCreated)
        ScheduledDownloadManager.destroyedSignal.connect(self.scheduledDownloadDestroyed)
        ScheduledDownloadManager.downloaderCountChangedSignal.connect(self.downloaderCountChanged)
        for scheduledDownloadId in ScheduledDownloadManager.getScheduledDownloadKeys():
            self.scheduledDownloadCreated(scheduledDownloadId)

    def showEnableState(self):
        enabled = ScheduledDownloadManager.isEnabled()
        self.enableButton.setIcon(QtGui.QIcon(Icons.TOGGLE_ON_ICON if ScheduledDownloadManager.isEnabled() else Icons.TOGGLE_OFF_ICON))
        if not enabled:
            self.enableButton.setEnabled(not ScheduledDownloadManager.isDownloaderRunning())

    def downloaderCountChanged(self):
        self.showEnableState()
        self.showStats()

    def enableButtonClicked(self):
        if ScheduledDownloadManager.isEnabled():
            if len(ScheduledDownloadManager.getScheduledDownloads()) != 0:
                if not self.ask("warning", "#This disables all scheduled downloads and disconnects from the channel.\nProceed?"):
                    return
                if ScheduledDownloadManager.isDownloaderRunning():
                    if not self.ask(*Messages.ASK.STOP_CANCEL_ALL_DOWNLOADS):
                        return
        ScheduledDownloadManager.setEnabled(not ScheduledDownloadManager.isEnabled())

    def addScheduledDownload(self):
        scheduledDownloadPreset = Ui.ScheduledDownloadSettings(parent=self).exec()
        if scheduledDownloadPreset != False:
            ScheduledDownloadManager.create(scheduledDownloadPreset)

    def scheduledDownloadCreated(self, scheduledDownloadId):
        item = PreviewWidgetItem(scheduledDownloadId=scheduledDownloadId)
        self.previewItems[scheduledDownloadId] = item
        self.previewWidgetView.setMinimumWidth(item.sizeHint().width() + self.previewWidgetView.verticalScrollBar().sizeHint().width())
        self.previewWidgetView.addItem(item)
        self.previewWidgetView.setItemWidget(item, item.widget)
        self.showStats()

    def scheduledDownloadDestroyed(self, scheduledDownloadId):
        self.previewWidgetView.takeItem(self.previewWidgetView.row(self.previewItems.pop(scheduledDownloadId)))
        self.showStats()

    def showStats(self):
        scheduledDownloadsCount = len(ScheduledDownloadManager.getScheduledDownloads())
        self.totalCount.setText(scheduledDownloadsCount)
        self.downloadingCount.setText(len(ScheduledDownloadManager.getRunningScheduledDownloads()))
        self.stackedWidget.setCurrentIndex(0 if scheduledDownloadsCount == 0 else 1)