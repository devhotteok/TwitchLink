from Core.Ui import *
from Services.Messages import Messages
from Services.PartnerContent.PartnerContentInFeedWidgetListViewer import PartnerContentInFeedWidgetListViewer

import uuid


class ScheduledDownloads(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.previewWidgets = {}
        self._ui = UiLoader.load("scheduledDownloads", self)
        self.showEnableState()
        self._ui.enableButton.clicked.connect(self.enableButtonClicked)
        self._ui.infoIcon = Utils.setSvgIcon(self._ui.infoIcon, Icons.SCHEDULED_ICON)
        self._ui.stackedWidget.setStyleSheet(f"#stackedWidget {{background-color: {self._ui.stackedWidget.palette().color(QtGui.QPalette.ColorGroup.Normal, QtGui.QPalette.ColorRole.Base).name()};}}")
        self._widgetListViewer = PartnerContentInFeedWidgetListViewer(self._ui.previewWidgetView, partnerContentSize=QtCore.QSize(320, 100), parent=self)
        self.showStats()
        self._ui.addScheduledDownloadButton.clicked.connect(self.addScheduledDownload)
        App.ScheduledDownloadManager.enabledChangedSignal.connect(self.showEnableState)
        App.ScheduledDownloadManager.createdSignal.connect(self.scheduledDownloadCreated)
        App.ScheduledDownloadManager.destroyedSignal.connect(self.scheduledDownloadDestroyed)
        App.ScheduledDownloadManager.downloaderCountChangedSignal.connect(self.downloaderCountChanged)
        self._widgetListViewer.setAutoReloadEnabled(False)
        for scheduledDownloadId in App.ScheduledDownloadManager.getScheduledDownloadKeys():
            self.scheduledDownloadCreated(scheduledDownloadId)
        self._widgetListViewer.setAutoReloadEnabled(True)

    def showEnableState(self) -> None:
        enabled = App.ScheduledDownloadManager.isEnabled()
        self._ui.enableButton.setIcon(QtGui.QIcon(Icons.TOGGLE_ON_ICON if App.ScheduledDownloadManager.isEnabled() else Icons.TOGGLE_OFF_ICON))
        if not enabled:
            self._ui.enableButton.setEnabled(not App.ScheduledDownloadManager.isDownloaderRunning())

    def downloaderCountChanged(self) -> None:
        self.showEnableState()
        self.showStats()

    def enableButtonClicked(self) -> None:
        if App.ScheduledDownloadManager.isEnabled():
            if len(App.ScheduledDownloadManager.getScheduledDownloads()) != 0:
                if not Utils.ask("warning", "#This disables all scheduled downloads and disconnects from the channel.\nProceed?", parent=self):
                    return
                if App.ScheduledDownloadManager.isDownloaderRunning():
                    if not Utils.ask(*Messages.ASK.STOP_CANCEL_ALL_DOWNLOADS, parent=self):
                        return
        App.ScheduledDownloadManager.setEnabled(not App.ScheduledDownloadManager.isEnabled())

    def addScheduledDownload(self) -> None:
        scheduledDownloadSettings = Ui.ScheduledDownloadSettings(parent=self)
        scheduledDownloadSettings.scheduledDownloadUpdated.connect(App.ScheduledDownloadManager.create, QtCore.Qt.ConnectionType.QueuedConnection)
        scheduledDownloadSettings.exec()

    def scheduledDownloadCreated(self, scheduledDownloadId: uuid.UUID) -> None:
        previewWidget = Ui.ScheduledDownloadPreview(scheduledDownloadId, parent=None)
        self.previewWidgets[scheduledDownloadId] = previewWidget
        self._widgetListViewer.addWidget(previewWidget, resizeSignal=previewWidget.resizedSignal)
        self.showStats()

    def scheduledDownloadDestroyed(self, scheduledDownloadId: uuid.UUID) -> None:
        self._widgetListViewer.removeWidget(self.previewWidgets.pop(scheduledDownloadId))
        self.showStats()

    def showStats(self) -> None:
        scheduledDownloadsCount = len(App.ScheduledDownloadManager.getScheduledDownloads())
        self._ui.totalCount.setText(scheduledDownloadsCount)
        self._ui.downloadingCount.setText(len(App.ScheduledDownloadManager.getRunningScheduledDownloads()))
        self._ui.stackedWidget.setCurrentIndex(0 if scheduledDownloadsCount == 0 else 1)