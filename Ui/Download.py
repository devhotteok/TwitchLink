from Core.Ui import *
from Services.Messages import Messages
from Services import ContentManager
from Services.Twitch.GQL import TwitchGQLAPI
from Services.Twitch.Playback import TwitchPlaybackGenerator
from Download.Downloader import TwitchDownloader
from Download.Downloader.Core.StreamDownloader import StreamDownloader
from Download.Downloader.Core.VideoDownloader import VideoDownloader
from Download.Downloader.Core.ClipDownloader import ClipDownloader
from Download import ScheduledDownloadPreset
from Ui.Components.Widgets.UpdateTrackInfoDisplay import UpdateTrackInfoDisplay
from Ui.Components.Widgets.RetryDownloadButton import RetryDownloadButton

import uuid


class Download(QtWidgets.QWidget):
    accountPageShowRequested = QtCore.pyqtSignal()

    def __init__(self, downloaderId: uuid.UUID, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.downloaderId = downloaderId
        self._downloader: StreamDownloader | VideoDownloader | ClipDownloader | None = None
        self._ui = UiLoader.load("download", self)
        self._ui.downloadViewControlBar = Utils.setPlaceholder(self._ui.downloadViewControlBar, Ui.DownloadViewControlBar(parent=self))
        self._ui.downloadViewControlBar.openLogsButton.clicked.connect(self.openLogs)
        self._ui.downloadInfoView = Utils.setPlaceholder(self._ui.downloadInfoView, Ui.DownloadInfoView(parent=self))
        self._ui.downloadInfoView.setThumbnailImageSizePolicy(QtCore.QSize(480, 270), QtCore.QSize(1920, 1080))
        self._ui.downloadInfoView.setCategoryImageSize(QtCore.QSize(45, 60))
        self._ui.alertIcon = Utils.setSvgIcon(self._ui.alertIcon, Icons.ALERT_RED)
        self._ui.statusInfoButton.clicked.connect(self.showErrorInfo)
        Utils.setIconViewer(self._ui.statusInfoButton, Icons.HELP)
        self._updateTrackInfoDisplay = UpdateTrackInfoDisplay(target=self._ui.updateTrackInfo, parent=self)
        self._ui.pauseButton.clicked.connect(self.pauseResume)
        self._ui.cancelButton.clicked.connect(self.cancel)
        self._ui.finishButton.clicked.connect(self.finishEarly)
        self._ui.openFolderButton.clicked.connect(self.openFolder)
        Utils.setIconViewer(self._ui.openFolderButton, Icons.FOLDER)
        self._ui.openFileButton.clicked.connect(self.openFile)
        Utils.setIconViewer(self._ui.openFileButton, Icons.FILE)
        self._downloader: StreamDownloader | VideoDownloader | ClipDownloader | None = None
        self._exception: Exception | None = None
        self.connectDownloader(App.DownloadManager.get(downloaderId))

    def connectDownloader(self, downloader: StreamDownloader | VideoDownloader | ClipDownloader) -> None:
        self.disconnectDownloader()
        self._downloader = downloader
        self._ui.downloadInfoView.showDownloadInfo(self._downloader.downloadInfo)
        self._ui.downloadViewControlBar.showDownloadInfo(self._downloader.downloadInfo)
        self._ui.downloadViewControlBar.openLogsButton.setCreating()
        self.setWindowTitle(self._downloader.downloadInfo.content.title)
        self._ui.windowTitleLabel.setText(self._downloader.downloadInfo.content.title)
        self._updateTrackInfoDisplay.connectDownloader(self._downloader)
        self._retryButtonManager = RetryDownloadButton(
            downloadInfo=self._downloader.downloadInfo,
            button=self._ui.retryButton,
            buttonIcon=Icons.RETRY,
            buttonText=self._ui.retryButton.text(),
            downloaderId=self.downloaderId,
            parent=self
        )
        self._retryButtonManager.accountPageShowRequested.connect(self.accountPageShowRequested)
        self._ui.retryButton.hide()
        self._ui.openFileButton.hide()
        self._ui.cancelButton.show()
        if isinstance(self._downloader, StreamDownloader):
            self._ui.pauseButton.hide()
            self._ui.finishButton.show()
        elif isinstance(self._downloader, VideoDownloader):
            self._ui.pauseButton.show()
            self._ui.finishButton.show()
        else:
            self._ui.pauseButton.hide()
            self._ui.finishButton.hide()
            self._ui.durationLabel.hide()
            self._ui.duration.hide()
            self._ui.mutedInfo.hide()
            self._ui.skippedInfo.hide()
            self._ui.missingInfo.hide()
        self._downloader.status.updated.connect(self._updateStatus)
        self._downloader.progress.updated.connect(self._updateProgress)
        self._downloader.finished.connect(self._downloadFinishHandler)
        self._updateStatus()
        self._updateProgress()
        if self._downloader.isFinished():
            self._downloadFinishHandler()

    def disconnectDownloader(self) -> None:
        if self._downloader != None:
            self._updateTrackInfoDisplay.disconnectDownloader()
            self._retryButtonManager.deleteLater()
            self._retryButtonManager = None
            self._downloader.status.updated.disconnect(self._updateStatus)
            self._downloader.progress.updated.disconnect(self._updateProgress)
            self._downloader.finished.disconnect(self._downloadFinishHandler)
            self._ui.downloadViewControlBar.openLogsButton.setHidden()
            self._ui.retryButton.hide()
            self._ui.pauseButton.hide()
            self._ui.cancelButton.hide()
            self._ui.finishButton.hide()
            self._ui.openFileButton.hide()
            self._downloader = None

    def _updateStatus(self) -> None:
        if self._downloader.status.pauseState.isFalse():
            self._ui.pauseButton.setText(T("pause"))
        if self._downloader.status.terminateState.isInProgress():
            self.showStatus(T("stopping" if getattr(self._downloader, "isFinishingEarly", False) else "canceling", ellipsis=True))
            self._ui.pauseButton.setEnabled(False)
            self._ui.cancelButton.setEnabled(False)
            self._ui.finishButton.setEnabled(False)
        elif not self._downloader.status.pauseState.isFalse():
            if self._downloader.status.pauseState.isInProgress():
                self.showStatus(T("pausing", ellipsis=True))
                self._ui.pauseButton.setEnabled(False)
                self._ui.pauseButton.setText(T("pausing", ellipsis=True))
            else:
                self.showAlert(T("paused"))
                self._ui.pauseButton.setEnabled(True)
                self._ui.pauseButton.setText(T("resume"))
        elif self._downloader.status.isPreparing():
            self.showStatus(T("preparing", ellipsis=True))
        elif self._downloader.status.isDownloading():
            self.showStatus(T("live-downloading" if isinstance(self._downloader, StreamDownloader) else "downloading", ellipsis=True))

        if self._downloader.status.isDone():
            if self._downloader.status.terminateState.isTrue():
                if isinstance(self._downloader.status.getError(), Exceptions.AbortRequested):
                    if getattr(self._downloader, "isFinishingEarly", False):
                        self.showStatus(T("download-stopped"))
                        self.showProgress(100)
                    else:
                        self.showAlert(T("download-canceled"))
                elif self._downloader.status.getError() != None:
                    self.showAlert(T("download-aborted"))
            elif self._downloader.status.getError() != None:
                self.showAlert(T("download-aborted"))
            else:
                self.showStatus(T("download-completed"))
                self.showProgress(100)

        if self._downloader.status.isFileRemoved():
            self._ui.openFolderButton.hide()
        else:
            self._ui.openFolderButton.show()

        if self._downloader.status.isDone() and not self._downloader.status.isFileRemoved() and self._downloader.status.getError() == None:
            self._ui.openFileButton.show()
        
        self._ui.downloadViewControlBar.openLogsButton.setVisible()
        
        if self._downloader.status.isDone():
            self._ui.pauseButton.hide()
            self._ui.cancelButton.hide()
            self._ui.finishButton.hide()

    def _updateProgress(self) -> None:
        if self._downloader.status.isPreparing():
            self.showProgress(0)
        elif isinstance(self._downloader, StreamDownloader):
            if self._downloader.status.isDone():
                pass  # progress already handled by _updateStatus / _downloadFinishHandler
            else:
                self.showProgress(None)
        elif isinstance(self._downloader, VideoDownloader):
            if self._downloader.status.isDownloading() and not self._downloader.status.pauseState.isTrue():
                if self._downloader.downloadInfo.isUpdateTrackEnabled() and self._downloader.status.getWaitingCount() != -1:
                    self.showProgress(None)
                else:
                    self.showProgress(self._downloader.progress.fileProgress)
        else:
            self.showProgress(self._downloader.progress.sizeProgress)
        self._updateDurationInfo()
        self._ui.fileSize.setText(self._downloader.progress.size)

    def _updateDurationInfo(self) -> None:
        if isinstance(self._downloader, StreamDownloader):
            self._ui.downloadInfoView.updateDurationInfo(self._downloader.progress.milliseconds)
            self._ui.duration.setText(Utils.formatMilliseconds(self._downloader.progress.milliseconds))
        elif isinstance(self._downloader, VideoDownloader):
            self._ui.downloadInfoView.updateDurationInfo(
                totalMilliseconds=int(self._downloader.downloadInfo.content.lengthSeconds * 1000),
                progressMilliseconds=self._downloader.progress.milliseconds,
                cropRangeMilliseconds=self._downloader.downloadInfo.getCropRangeMilliseconds()
            )
            self._ui.duration.setText(f"{Utils.formatMilliseconds(self._downloader.progress.milliseconds)} / {Utils.formatMilliseconds(self._downloader.progress.totalMilliseconds)}")
        elif isinstance(self._downloader, ClipDownloader):
            return
        self._ui.downloadInfoView.showMutedInfo(self._downloader.progress.mutedFiles, self._downloader.progress.mutedMilliseconds)
        self._ui.downloadInfoView.showSkippedInfo(self._downloader.progress.skippedFiles + getattr(self._downloader.progress, 'adFiles', 0), self._downloader.progress.skippedMilliseconds + getattr(self._downloader.progress, 'adMilliseconds', 0))
        self._ui.downloadInfoView.showMissingInfo(self._downloader.progress.missingFiles, self._downloader.progress.missingMilliseconds)
        if self._downloader.progress.mutedFiles == 0:
            self._ui.mutedInfo.hide()
        else:
            self._ui.mutedInfo.setText(T("errors.#failed_unmute_segments", fileCount=self._downloader.progress.mutedFiles, time=Utils.formatMilliseconds(self._downloader.progress.mutedMilliseconds)))
            self._ui.mutedInfo.show()
        total_skipped = self._downloader.progress.skippedFiles + getattr(self._downloader.progress, 'adFiles', 0)
        total_skipped_ms = self._downloader.progress.skippedMilliseconds + getattr(self._downloader.progress, 'adMilliseconds', 0)
        if total_skipped == 0:
            self._ui.skippedInfo.hide()
        else:
            self._ui.skippedInfo.setText(T("messages.#skipped_commercial_segments", fileCount=total_skipped, time=Utils.formatMilliseconds(total_skipped_ms)))
            self._ui.skippedInfo.show()
        if self._downloader.progress.missingFiles == 0:
            self._ui.missingInfo.hide()
        else:
            self._ui.missingInfo.setText(T("errors.#missing_segments", fileCount=self._downloader.progress.missingFiles, time=Utils.formatMilliseconds(self._downloader.progress.missingMilliseconds)))
            self._ui.missingInfo.show()

    def _downloadFinishHandler(self) -> None:
        if self._downloader.status.terminateState.isTrue():
            if isinstance(self._downloader.status.getError(), Exceptions.AbortRequested):
                if getattr(self._downloader, "isFinishingEarly", False):
                    self.showStatus(T("download-stopped"))
                    self.showProgress(100)
                elif isinstance(self._downloader, StreamDownloader):
                    self.showStatus(T("download-stopped"))
                    self.showProgress(100)
                else:
                    self.showAlert(T("download-canceled"))
                    self._ui.retryButton.show()
            else:
                self.showError(self._downloader.status.getError(), downloadAborted=True)
                self._ui.retryButton.show()
        else:
            self.showStatus(T("download-completed"))
            self.showProgress(100)
        if not self._downloader.status.isFileRemoved():
            self._ui.openFileButton.show()
        self._ui.downloadViewControlBar.openLogsButton.setVisible()
        self._ui.pauseButton.hide()
        self._ui.cancelButton.hide()
        self._ui.finishButton.hide()

    def showStatus(self, status: str) -> None:
        self._ui.alertIcon.hide()
        self._ui.status.setText(status)
        self._ui.statusInfoButton.hide()
        self._ui.progressBar.clearState()

    def showProgress(self, progress: int | None) -> None:
        if progress == None:
            self._ui.progressBar.setRange(0, 0)
        else:
            self._ui.progressBar.setRange(0, 100)
            self._ui.progressBar.setValue(progress)

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
                Utils.info("process-error", "errors.#process_exited_unexpectedly_possible_ca", parent=self)
            elif isinstance(self._exception, TwitchGQLAPI.Exceptions.AuthorizationError):
                if App.Account.isSignedIn():
                    Utils.info(*Messages.INFO.AUTHENTICATION_ERROR, parent=self)
                else:
                    Utils.info(*Messages.INFO.TEMPORARY_ERROR, parent=self)
            else:
                Utils.info("error", "errors.#an_error_occurred_while_downloading", parent=self)
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
            if App.Account.isSignedIn():
                return f"{T("errors.#authentication_your_account_has_been_de")}\n\n{T('reason')}: {self._exception.reason}"
            else:
                return f"{T("errors.#authentication_denied")}\n\n{T('reason')}: {self._exception.reason}"
        elif isinstance(self._exception, TwitchPlaybackGenerator.Exceptions.GeoBlock):
            return f"{T("info.#this_content_is_not_available_your_regi")}\n\n{T('reason')}: {self._exception.reason}"
        elif isinstance(self._exception, TwitchPlaybackGenerator.Exceptions.ChannelNotFound):
            return T("errors.#channel_not_found_deleted_or_temporary")
        elif isinstance(self._exception, ContentManager.Exceptions.RestrictedContent):
            if self._exception.restrictionType == ContentManager.RestrictionType.CONTENT_TYPE:
                restrictionType = T("errors.#downloading_this_channel_has_been_restr", channel=self._exception.channel.displayName, contentType=T(self._exception.contentType))
            else:
                restrictionType = T("errors.#this_content_has_been_restricted_stream", channel=self._exception.channel.displayName)
            restrictionInfo = T("messages.#to_protect_rights_streamers_restricts_d", appName=Config.APP_NAME)
            message = f"{restrictionType}\n\n{restrictionInfo}"
            if self._exception.reason != None:
                message = f"{message}\n\n[{T('reason')}]\n{self._exception.reason}"
            return message
        elif isinstance(self._exception, ScheduledDownloadPreset.Exceptions.PreferredResolutionNotFound):
            return T("errors.#the_preferred_resolution_was_not_found")
        elif isinstance(self._exception, TwitchDownloader.Exceptions.DownloaderCreationDisabled):
            return T("errors.#unable_start_new_download_this_feature")
        else:
            return None

    def pauseResume(self) -> None:
        if self._downloader.status.pauseState.isFalse():
            self._downloader.pause()
        else:
            self._downloader.resume()

    def cancel(self) -> None:
        if Utils.ask(*Messages.ASK.CANCEL_DOWNLOAD, parent=self):
            self._downloader.cancel()
            if self._downloader.status.terminateState.isFalse():
                Utils.info(*Messages.INFO.ACTION_PERFORM_ERROR, parent=self)

    def finishEarly(self) -> None:
        if Utils.ask(*Messages.ASK.STOP_DOWNLOAD, parent=self):
            if hasattr(self._downloader, "finishEarly"):
                self._downloader.finishEarly()
            if self._downloader.status.terminateState.isFalse():
                Utils.info(*Messages.INFO.ACTION_PERFORM_ERROR, parent=self)

    def openFolder(self) -> None:
        if not Utils.openFolder(self._downloader.downloadInfo.getAbsoluteDirectory()):
            Utils.info(*Messages.INFO.FOLDER_NOT_FOUND, parent=self)

    def openFile(self) -> None:
        if not Utils.openFile(self._downloader.downloadInfo.getAbsoluteFileName()):
            Utils.info(*Messages.INFO.FILE_NOT_FOUND, parent=self)

    def openLogs(self) -> None:
        if not Utils.openFile(self._downloader.logger.getPath()):
            Utils.info(*Messages.INFO.FILE_NOT_FOUND, parent=self)

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self._ui.retranslateUi(self)
            self.retranslateDynamicUi()

    def retranslateDynamicUi(self) -> None:
        pass
