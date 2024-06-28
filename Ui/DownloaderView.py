from Core.Ui import *
from Services.Messages import Messages
from Services import ContentManager
from Services.Twitch.GQL import TwitchGQLAPI
from Services.Twitch.GQL.TwitchGQLModels import Channel, Stream, Video, Clip
from Services.Twitch.Playback import TwitchPlaybackGenerator
from Download.DownloadInfo import DownloadInfo
from Download.Downloader import TwitchDownloader
from Download.Downloader.Core.StreamDownloader import StreamDownloader
from Download.Downloader.Core.VideoDownloader import VideoDownloader
from Download.Downloader.Core.ClipDownloader import ClipDownloader
from Download import ScheduledDownloadPreset
from Ui.Components.Widgets.UpdateTrackInfoDisplay import UpdateTrackInfoDisplay


class DownloaderView(QtWidgets.QWidget):
    resizedSignal = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("downloaderView", self)
        self._ui.downloadInfoView = Utils.setPlaceholder(self._ui.downloadInfoView, Ui.DownloadInfoView(parent=self))
        self._ui.alertIcon = Utils.setSvgIcon(self._ui.alertIcon, Icons.ALERT_RED)
        self._ui.statusInfoButton.clicked.connect(self.showErrorInfo)
        Utils.setIconViewer(self._ui.statusInfoButton, Icons.HELP)
        self._updateTrackInfoDisplay = UpdateTrackInfoDisplay(target=self._ui.updateTrackInfo, parent=self)
        self._downloader: StreamDownloader | VideoDownloader | ClipDownloader | None = None
        self._exception: Exception | None = None
        self.setStatusVisible(False)

    def connectDownloader(self, downloader: StreamDownloader | VideoDownloader | ClipDownloader) -> None:
        self.disconnectDownloader()
        self._downloader = downloader
        self._ui.downloadInfoView.showDownloadInfo(self._downloader.downloadInfo)
        self._updateTrackInfoDisplay.connectDownloader(self._downloader)
        self._downloader.status.updated.connect(self._updateStatus)
        self._downloader.progress.updated.connect(self._updateProgress)
        self._downloader.finished.connect(self._downloadFinishHandler)
        self._updateStatus()
        self._updateProgress()
        if self._downloader.isFinished():
            self._downloadFinishHandler()
        self.setStatusVisible(True)

    def disconnectDownloader(self) -> None:
        if self._downloader != None:
            self._updateTrackInfoDisplay.disconnectDownloader()
            self._downloader.status.updated.disconnect(self._updateStatus)
            self._downloader.progress.updated.disconnect(self._updateProgress)
            self._downloader.finished.disconnect(self._downloadFinishHandler)
            self._downloader = None

    def setStatusVisible(self, visible: bool) -> None:
        self._ui.statusArea.setVisible(visible)
        self.resizedSignal.emit()

    def _updateStatus(self) -> None:
        if self._downloader.status.terminateState.isInProgress():
            self.showStatus(T("stopping" if isinstance(self._downloader, StreamDownloader) else "canceling", ellipsis=True))
        elif not self._downloader.status.pauseState.isFalse():
            if self._downloader.status.pauseState.isInProgress():
                self.showStatus(T("pausing", ellipsis=True))
            else:
                self.showAlert(T("paused"))
        elif self._downloader.status.isPreparing():
            self.showStatus(T("preparing", ellipsis=True))
        elif self._downloader.status.isDownloading():
            self.showStatus(T("live-downloading" if isinstance(self._downloader, StreamDownloader) else "downloading", ellipsis=True))

    def _updateProgress(self) -> None:
        if self._downloader.status.isPreparing():
            self.showProgress(0)
        elif isinstance(self._downloader, StreamDownloader):
            self.showProgress(None, self._downloader.progress.size)
        elif isinstance(self._downloader, VideoDownloader):
            if self._downloader.status.isDownloading() and not self._downloader.status.pauseState.isTrue():
                if self._downloader.downloadInfo.isUpdateTrackEnabled() and self._downloader.status.getWaitingCount() != -1:
                    self.showProgress(None, self._downloader.progress.size)
                else:
                    self.showProgress(self._downloader.progress.fileProgress, self._downloader.progress.size)
        else:
            self.showProgress(self._downloader.progress.sizeProgress, self._downloader.progress.size)
        self._updateDurationInfo()

    def _updateDurationInfo(self) -> None:
        if isinstance(self._downloader, StreamDownloader):
            self._ui.downloadInfoView.updateDurationInfo(self._downloader.progress.milliseconds)
        elif isinstance(self._downloader, VideoDownloader):
            self._ui.downloadInfoView.updateDurationInfo(
                totalMilliseconds=int(self._downloader.downloadInfo.content.lengthSeconds * 1000),
                progressMilliseconds=self._downloader.progress.milliseconds,
                cropRangeMilliseconds=self._downloader.downloadInfo.getCropRangeMilliseconds()
            )
        elif isinstance(self._downloader, ClipDownloader):
            return
        self._ui.downloadInfoView.showMutedInfo(self._downloader.progress.mutedFiles, self._downloader.progress.mutedMilliseconds)
        self._ui.downloadInfoView.showSkippedInfo(self._downloader.progress.skippedFiles, self._downloader.progress.skippedMilliseconds)
        self._ui.downloadInfoView.showMissingInfo(self._downloader.progress.missingFiles, self._downloader.progress.missingMilliseconds)

    def _downloadFinishHandler(self) -> None:
        if self._downloader.status.terminateState.isTrue():
            if isinstance(self._downloader.status.getError(), Exceptions.AbortRequested):
                if isinstance(self._downloader, StreamDownloader):
                    self.setStatusVisible(False)
                else:
                    self.showAlert(T("download-canceled"))
            else:
                self.showError(self._downloader.status.getError(), downloadAborted=True)
        else:
            self.setStatusVisible(False)

    def showStatus(self, status: str) -> None:
        self._ui.alertIcon.hide()
        self._ui.status.setText(status)
        self._ui.statusInfoButton.hide()
        self._ui.progressBar.clearState()

    def showProgress(self, progress: int | None, fileSize: str | None = None) -> None:
        if progress == None:
            self._ui.progressBar.setRange(0, 0)
        else:
            self._ui.progressBar.setRange(0, 100)
            self._ui.progressBar.setValue(progress)
        if fileSize == None:
            self._ui.fileSize.hide()
        else:
            self._ui.fileSize.setText(fileSize)
            self._ui.fileSize.show()

    def showAlert(self, text: str) -> None:
        self._ui.alertIcon.show()
        self._ui.status.setText(text)
        self._ui.statusInfoButton.hide()
        self._ui.progressBar.showWarning()
        self.showProgress(100)

    def showError(self, exception: Exception | None, downloadAborted: bool = False) -> None:
        self._exception = exception
        if self._exception != None:
            self._ui.alertIcon.show()
            reasonText = self._getErrorReason()
            self._ui.status.setText(f"{T('download-aborted')} ({T(reasonText)})" if downloadAborted else T(reasonText))
            self._ui.statusInfoButton.show()
            self._ui.progressBar.showError()
            self.showProgress(100)

    def showErrorInfo(self) -> None:
        description = self._getErrorDescription()
        if description == None:
            if isinstance(self._exception, Exceptions.FileSystemError):
                Utils.info(*Messages.INFO.FILE_SYSTEM_ERROR, parent=self)
            elif isinstance(self._exception, Exceptions.NetworkError):
                Utils.info(*Messages.INFO.NETWORK_ERROR, parent=self)
            elif isinstance(self._exception, Exceptions.ProcessError):
                Utils.info("process-error", "#Process exited unexpectedly.\n\nPossible Causes\n\n* Corruption of the original file\n* Invalid crop range\n* Too long or invalid filename or path\n* Out of memory\n* Out of storage capacity\n* Lack of device performance\n* Needs permission to perform this action\n\nIf the error persists, try Run as administrator.", parent=self)
            elif isinstance(self._exception, TwitchGQLAPI.Exceptions.AuthorizationError):
                if App.Account.isLoggedIn():
                    Utils.info(*Messages.INFO.AUTHENTICATION_ERROR, parent=self)
                else:
                    Utils.info(*Messages.INFO.TEMPORARY_ERROR, parent=self)
            else:
                Utils.info("error", "#An error occurred while downloading.", parent=self)
        else:
            Utils.info("unable-to-download", description, contentTranslate=False, parent=self)

    def _getErrorReason(self) -> str:
        if isinstance(self._exception, Exceptions.FileSystemError):
            return "system-error"
        elif isinstance(self._exception, Exceptions.NetworkError):
            return "network-error"
        elif isinstance(self._exception, Exceptions.ProcessError):
            return "process-error"
        elif isinstance(self._exception, ContentManager.Exceptions.RestrictedContent):
            return "restricted-content"
        elif isinstance(self._exception, ScheduledDownloadPreset.Exceptions.PreferredResolutionNotFound):
            return "preferred-resolution-not-found"
        elif isinstance(self._exception, TwitchDownloader.Exceptions.DownloaderCreationDisabled):
            return "disabled-feature"
        else:
            return "unexpected-error"

    def _getErrorDescription(self) -> str | None:
        if isinstance(self._exception, TwitchPlaybackGenerator.Exceptions.Forbidden):
            if App.Account.isLoggedIn():
                return f"{T('#Authentication of your account has been denied.')}\n\n{T('reason')}: {self._exception.reason}"
            else:
                return f"{T('#Authentication denied.')}\n\n{T('reason')}: {self._exception.reason}"
        elif isinstance(self._exception, TwitchPlaybackGenerator.Exceptions.GeoBlock):
            return f"{T('#This content is not available in your region.')}\n\n{T('reason')}: {self._exception.reason}"
        elif isinstance(self._exception, TwitchPlaybackGenerator.Exceptions.ChannelNotFound):
            return T("#Channel not found. Deleted or temporary error.")
        elif isinstance(self._exception, ContentManager.Exceptions.RestrictedContent):
            if self._exception.restrictionType == ContentManager.RestrictionType.CONTENT_TYPE:
                restrictionType = T("#Downloading {contentType} from this channel has been restricted by the streamer({channel})'s request or by the administrator.", channel=self._exception.channel.displayName, contentType=T(self._exception.contentType))
            else:
                restrictionType = T("#This content has been restricted by the streamer({channel})'s request or by the administrator.", channel=self._exception.channel.displayName)
            restrictionInfo = T("#To protect the rights of streamers, {appName} restricts downloads when a content restriction request is received.", appName=Config.APP_NAME)
            message = f"{restrictionType}\n\n{restrictionInfo}"
            if self._exception.reason != None:
                message = f"{message}\n\n[{T('reason')}]\n{self._exception.reason}"
            return message
        elif isinstance(self._exception, ScheduledDownloadPreset.Exceptions.PreferredResolutionNotFound):
            return T("#The preferred resolution was not found.\nYou have disabled the download until a matching resolution is found.")
        elif isinstance(self._exception, TwitchDownloader.Exceptions.DownloaderCreationDisabled):
            return T("#Unable to start a new download.\nThis feature has been disabled.")
        else:
            return None

    def updateContentInfo(self, content: Channel | Stream | Video | Clip | DownloadInfo | None, immediateRefresh: bool = True) -> None:
        if isinstance(content, DownloadInfo):
            self._ui.downloadInfoView.showDownloadInfo(content, immediateRefresh=immediateRefresh)
        else:
            self._ui.downloadInfoView.showContentInfo(content, immediateRefresh=immediateRefresh)
        if self._downloader != None:
            self._updateDurationInfo()