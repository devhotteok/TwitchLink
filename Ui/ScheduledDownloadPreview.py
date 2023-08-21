from Core.Ui import *
from Services.Messages import Messages
from Services.Twitch.GQL import TwitchGQLModels
from Download.Downloader.Core.StreamDownloader import StreamDownloader
from Download import ScheduledDownloadPreset
from Ui.Components.Widgets.WidgetRemoveController import WidgetRemoveController

import uuid


class ScheduledDownloadPreview(QtWidgets.QWidget):
    resizedSignal = QtCore.pyqtSignal()

    def __init__(self, scheduledDownloadId: uuid.UUID, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.scheduledDownloadId = scheduledDownloadId
        self._downloader: StreamDownloader | None = None
        self._widgetRemoveController = WidgetRemoveController(parent=self)
        self._widgetRemoveController.performRemove.connect(self.removeScheduledDownload)
        self._ui = UiLoader.load("scheduledDownloadPreview", self)
        self._ui.downloadViewControlBar = Utils.setPlaceholder(self._ui.downloadViewControlBar, Ui.DownloadViewControlBar(parent=self))
        self._ui.downloaderView = Utils.setPlaceholder(self._ui.downloaderView, Ui.DownloaderView(parent=self))
        self._ui.downloaderView.resizedSignal.connect(self.resizedSignal, QtCore.Qt.ConnectionType.QueuedConnection)
        self._ui.downloadViewControlBar.openFolderButton.clicked.connect(self.openFolder)
        self._ui.downloadViewControlBar.openFolderButton.setVisible()
        self._ui.downloadViewControlBar.openFileButton.clicked.connect(self.openFile)
        self._ui.downloadViewControlBar.openFileButton.setDisabled()
        self.scheduledDownload = App.ScheduledDownloadManager.get(self.scheduledDownloadId)
        self.scheduledDownload.activeChanged.connect(self._activeChanged)
        self._activeChanged()
        self.scheduledDownload.channelDataUpdateStarted.connect(self._channelDataUpdateStarted)
        self.scheduledDownload.channelDataUpdateFinished.connect(self._channelDataUpdateFinished)
        self.scheduledDownload.channelDataUpdated.connect(self._showChannel)
        self.scheduledDownload.pubSubStateChanged.connect(self._showPubSubState)
        self.scheduledDownload.status.updated.connect(self._statusUpdated)
        self._statusUpdated()
        if self.scheduledDownload.isUpdatingChannelData():
            self._channelDataUpdateStarted()
        else:
            self._channelDataUpdateFinished()
        self._showChannel()
        self._showPubSubState()
        self._ui.networkAlertIcon = Utils.setSvgIcon(self._ui.networkAlertIcon, Icons.ALERT_RED_ICON)
        self._ui.enableButton.clicked.connect(self._enableButtonClicked)
        self._ui.refreshButton.clicked.connect(self.scheduledDownload.updateChannelData)
        self._ui.settingsButton.clicked.connect(self.editScheduledDownload)
        self._ui.deleteButton.clicked.connect(self.tryRemoveScheduledDownload)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self.resizedSignal.emit()
        super().showEvent(event)

    def _activeChanged(self) -> None:
        self._ui.downloaderArea.setEnabled(self.scheduledDownload.isActive())
        self._ui.enableButton.setIcon(QtGui.QIcon(Icons.TOGGLE_ON_ICON if self.scheduledDownload.isEnabled() else Icons.TOGGLE_OFF_ICON))

    def _enableButtonClicked(self) -> None:
        if self.scheduledDownload.isActive():
            if self.scheduledDownload.status.isDownloading():
                if not Utils.ask(*Messages.ASK.STOP_DOWNLOAD, parent=self):
                    return
        self.scheduledDownload.setEnabled(not self.scheduledDownload.isEnabled())

    def _statusUpdated(self) -> None:
        if self.scheduledDownload.status.isNone():
            self._ui.downloaderView.setStatusVisible(False)
        elif self.scheduledDownload.status.isGeneratingPlayback():
            self._ui.downloaderView.showAlert(T("preparing", ellipsis=True))
            self._ui.downloaderView.setStatusVisible(True)
        elif self.scheduledDownload.status.isDownloading():
            self.connectDownloader(self.scheduledDownload.downloader)
        elif self.scheduledDownload.status.isError():
            self._ui.downloaderView.showError(self.scheduledDownload.status.getError())
            self._ui.downloaderView.setStatusVisible(True)
            if isinstance(self.scheduledDownload.status.getError(), ScheduledDownloadPreset.Exceptions.PreferredResolutionNotFound) and App.Preferences.general.isNotifyEnabled():
                App.Instance.notification.toastMessage(
                    title=T("preferred-resolution-not-found"),
                    message=f"{T('#Unable to start scheduled download for channel {channel}.', channel=self.scheduledDownload.channel.formattedName)}\n{T('started-at')}: {self.scheduledDownload.channel.stream.createdAt.toTimeZone(App.Preferences.localization.getTimezone()).toString('yyyy-MM-dd HH:mm:ss')}",
                    icon=App.Instance.notification.Icons.Warning
                )
        elif self.scheduledDownload.status.isDownloaderError():
            self._ui.downloaderView.showError(self.scheduledDownload.status.getError(), downloadAborted=True)
            self._ui.downloaderView.setStatusVisible(True)

    def connectDownloader(self, downloader: StreamDownloader) -> None:
        self.disconnectDownloader()
        self._widgetRemoveController.setRemoveEnabled(False)
        self._downloader = downloader
        self._downloader.status.updated.connect(self._handleDownloadStatus)
        self._downloader.finished.connect(self._handleDownloadResult)
        self._handleDownloadStatus()
        self._ui.downloadViewControlBar.showDownloadInfo(self._downloader.downloadInfo)
        self._ui.downloadViewControlBar.openFileButton.setVisible()
        self._ui.downloaderView.connectDownloader(self._downloader)

    def disconnectDownloader(self) -> None:
        if self._downloader != None:
            self._ui.downloaderView.disconnectDownloader()
            self._downloader.status.updated.disconnect(self._handleDownloadStatus)
            self._downloader.finished.disconnect(self._handleDownloadResult)
            self._downloader = None
            self._showChannel()
            self._ui.downloadViewControlBar.openFileButton.setDisabled()
            self._widgetRemoveController.setRemoveEnabled(True)

    def _handleDownloadStatus(self) -> None:
        if self._downloader.status.terminateState.isInProgress():
            self._ui.enableButton.setEnabled(False)
            self._ui.refreshButton.setEnabled(False)

    def _handleDownloadResult(self) -> None:
        if self._downloader.status.terminateState.isTrue():
            self._ui.enableButton.setEnabled(True)
            self._ui.refreshButton.setEnabled(True)
        self.disconnectDownloader()

    def _channelDataUpdateStarted(self) -> None:
        self._ui.refreshButton.setEnabled(False)
        if not self.scheduledDownload.isChannelRetrieved():
            self._showNetworkStatus(T("loading-channel-data", ellipsis=True))

    def _channelDataUpdateFinished(self) -> None:
        self._ui.refreshButton.setEnabled(True)
        if not self.scheduledDownload.isChannelRetrieved():
            self._showNetworkStatus(T("channel-not-found"))

    def _showChannel(self) -> None:
        if self.scheduledDownload.channel == None:
            target = TwitchGQLModels.Channel({"displayName": self.scheduledDownload.preset.channel})
        elif self.scheduledDownload.channel.stream == None:
            target = self.scheduledDownload.channel
        else:
            target = self.scheduledDownload.channel.stream
        if self._downloader == None:
            self._ui.downloadViewControlBar.showContentInfo(target)
            self._ui.downloaderView.updateContentInfo(target, immediateRefresh=False)
        elif isinstance(target, TwitchGQLModels.Stream):
            downloadInfo = self._downloader.downloadInfo.copy()
            downloadInfo.updateContent(target)
            self._ui.downloadViewControlBar.showDownloadInfo(downloadInfo)
            self._ui.downloaderView.updateContentInfo(downloadInfo, immediateRefresh=False)

    def _showPubSubState(self) -> None:
        if not self.scheduledDownload.isActive():
            self._showNetworkStatus(T("deactivated"))
        elif self.scheduledDownload.isSubscribed():
            self._showNetworkStatus()
        elif self.scheduledDownload.isConnecting():
            self._showNetworkStatus(T("connecting", ellipsis=True))
        else:
            self._showNetworkStatus(T("not-connected"))

    def _showNetworkStatus(self, text: str | None = None) -> None:
        if text == None:
            self._ui.networkStatusArea.hide()
        else:
            self._ui.networkStatusArea.show()
            self._ui.networkStatus.setText(text)
        self.resizedSignal.emit()

    def openFolder(self) -> None:
        try:
            Utils.openFolder(self.scheduledDownload.preset.directory)
        except:
            Utils.info(*Messages.INFO.FOLDER_NOT_FOUND, parent=self)

    def openFile(self) -> None:
        try:
            Utils.openFolder(self.scheduledDownload.downloader.downloadInfo.getAbsoluteFileName())
        except:
            Utils.info(*Messages.INFO.FOLDER_NOT_FOUND, parent=self)

    def editScheduledDownload(self) -> None:
        scheduledDownloadSettings = Ui.ScheduledDownloadSettings(self.scheduledDownload.preset, parent=self)
        scheduledDownloadSettings.scheduledDownloadUpdated.connect(self.scheduledDownload.updateChannelData, QtCore.Qt.ConnectionType.QueuedConnection)
        scheduledDownloadSettings.exec()

    def tryRemoveScheduledDownload(self) -> None:
        if self.scheduledDownload.isActive():
            if self.scheduledDownload.status.isDownloading():
                if not Utils.ask(*Messages.ASK.STOP_DOWNLOAD, parent=self):
                    return
            self.scheduledDownload.setEnabled(False)
        self._widgetRemoveController.registerRemove()
        self.setEnabled(False)

    def removeScheduledDownload(self) -> None:
        App.ScheduledDownloadManager.remove(self.scheduledDownloadId)