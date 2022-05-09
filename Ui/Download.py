from Core.Ui import *
from Services.Messages import Messages
from Download.DownloadManager import DownloadManager


class Download(QtWidgets.QWidget, UiFile.download):
    def __init__(self, downloaderId, parent=None):
        super(Download, self).__init__(parent=parent)
        self.downloader = DownloadManager.get(downloaderId)
        self.downloadInfo = self.downloader.setup.downloadInfo
        self.videoData = self.downloadInfo.videoData
        self.setWindowTitle(self.videoData.title)
        self.window_title.setText(self.videoData.title)
        self.category_image.loadImage(filePath=Images.CATEGORY_IMAGE, url=self.videoData.game.boxArtURL, urlFormatSize=ImageSize.CATEGORY)
        self.category.setText(self.videoData.game.displayName)
        self.title.setText(self.videoData.title)
        self.thumbnail_image.setImageSizePolicy((480, 270), (1920, 1080))
        if self.downloadInfo.type.isStream():
            self.liveLabel.setText(T("live" if self.videoData.isLive() else "rerun").upper())
            self.thumbnail_image.loadImage(filePath=Images.PREVIEW_IMAGE, url=self.videoData.previewImageURL, urlFormatSize=ImageSize.STREAM_PREVIEW, refresh=True)
            self.user_name.setText(self.videoData.broadcaster.displayName)
            self.date.setText(self.videoData.createdAt.asTimezone(DB.localization.getTimezone()))
            self.view_countInfo.setText(f"{T('viewer-count')}:")
            self.view_count.setText(self.videoData.viewersCount)
            self.tagArea.hide()
            self.downloadProgressBar.setRange(0, 0)
            self.encodingProgressBar.setRange(0, 0)
            self.pauseButton.hide()
            self.cancelButton.setText(T("stop"))
        elif self.downloadInfo.type.isVideo():
            self.liveLabelArea.hide()
            self.thumbnail_image.loadImage(filePath=Images.THUMBNAIL_IMAGE, url=self.videoData.previewThumbnailURL, urlFormatSize=ImageSize.VIDEO_THUMBNAIL)
            self.user_name.setText(self.videoData.owner.displayName)
            self.date.setText(self.videoData.publishedAt.asTimezone(DB.localization.getTimezone()))
            start, end = self.downloadInfo.range
            totalSeconds = self.videoData.lengthSeconds.totalSeconds()
            durationSeconds = (end or totalSeconds) - (start or 0)
            self.showVideoDuration(start, end, totalSeconds, durationSeconds)
            self.view_countInfo.setText(f"{T('view-count')}:")
            self.view_count.setText(self.videoData.viewCount)
            self.unmuteVideoTag.setVisible(self.downloadInfo.isUnmuteVideoEnabled())
            self.updateTrackTag.setVisible(self.downloadInfo.isUpdateTrackEnabled())
            self.prioritizeTag.setVisible(self.downloadInfo.isPrioritizeEnabled())
            self.skipWaitingButton.clicked.connect(self.skipWaiting)
            self.skipDownloadButton.clicked.connect(self.skipDownload)
            self.pauseButton.clicked.connect(self.pauseResume)
            self.cancelButton.setText(T("cancel"))
        else:
            self.liveLabelArea.hide()
            self.thumbnail_image.loadImage(filePath=Images.THUMBNAIL_IMAGE, url=self.videoData.thumbnailURL, urlFormatSize=ImageSize.CLIP_THUMBNAIL)
            self.user_name.setText(self.videoData.broadcaster.displayName)
            self.date.setText(self.videoData.createdAt.asTimezone(DB.localization.getTimezone()))
            self.duration.setText(self.videoData.durationSeconds)
            self.view_count.setText(self.videoData.viewCount)
            self.unmuteVideoTag.hide()
            self.updateTrackTag.hide()
            self.prioritizeTag.setVisible(self.downloadInfo.isPrioritizeEnabled())
            self.encodingLabel.hide()
            self.encodingProgressBar.hide()
            self.durationLabel.hide()
            self.currentDuration.hide()
            self.pauseButton.hide()
            self.cancelButton.setText(T("cancel"))
        self.resolution.setText(self.downloadInfo.resolution.displayName)
        self.file.setText(self.downloadInfo.getAbsoluteFileName())
        sizePolicy = self.skipWaitingButton.sizePolicy()
        sizePolicy.setRetainSizeWhenHidden(True)
        self.skipWaitingButton.setSizePolicy(sizePolicy)
        self.skipDownloadButton.setSizePolicy(sizePolicy)
        self.skipWaitingButton.hide()
        self.skipDownloadButton.hide()
        self.dataLoss.hide()
        self.cancelButton.clicked.connect(self.cancel)
        self.openFolderButton.clicked.connect(self.openFolder)
        self.openFileButton.clicked.connect(self.openFile)
        self.openFileButton.hide()
        self.openLogsButton.clicked.connect(self.openLogs)
        self.openLogsButton.hide()
        self.connectDownloader()

    def connectDownloader(self):
        self.downloader.finished.connect(self.handleDownloadResult)
        if self.downloadInfo.type.isStream():
            self.downloader.statusUpdate.connect(self.handleStreamStatus)
            self.downloader.progressUpdate.connect(self.handleStreamProgress)
            self.handleStreamStatus(self.downloader.status)
            self.handleStreamProgress(self.downloader.progress)
        elif self.downloadInfo.type.isVideo():
            self.downloader.statusUpdate.connect(self.handleVideoStatus)
            self.downloader.progressUpdate.connect(self.handleVideoProgress)
            self.downloader.dataUpdate.connect(self.handleVideoDataUpdate)
            self.handleVideoStatus(self.downloader.status)
            self.handleVideoProgress(self.downloader.progress)
        else:
            self.downloader.statusUpdate.connect(self.handleClipStatus)
            self.downloader.progressUpdate.connect(self.handleClipProgress)
            self.handleClipStatus(self.downloader.status)
            self.handleClipProgress(self.downloader.progress)
        if self.downloader.isFinished():
            self.handleDownloadResult()

    def skipWaiting(self):
        self.downloader.skipWaiting()

    def skipDownload(self):
        if self.ask("warning", "#This will skip the rest of the download and encode the already downloaded part.\nProceed?"):
            if self.skipDownloadButton.isVisible() and self.skipDownloadButton.isEnabled():
                self.downloader.skipDownload()
            else:
                self.info(*Messages.INFO.ACTION_PERFORM_ERROR)

    def pauseResume(self):
        if self.downloader.status.pauseState.isFalse():
            self.downloader.pause()
        else:
            self.downloader.resume()
            self.pauseButton.setText(T("pause"))

    def cancel(self):
        if self.ask(*(Messages.ASK.STOP_DOWNLOAD if self.downloadInfo.type.isStream() else Messages.ASK.CANCEL_DOWNLOAD)):
            self.downloader.cancel()
            if self.downloader.status.terminateState.isFalse():
                self.info(*Messages.INFO.ACTION_PERFORM_ERROR)

    def openFolder(self):
        try:
            Utils.openFolder(self.downloadInfo.directory)
        except:
            self.info(*Messages.INFO.FOLDER_NOT_FOUND)

    def openFile(self):
        try:
            Utils.openFile(self.downloadInfo.getAbsoluteFileName())
        except:
            self.info(*Messages.INFO.FILE_NOT_FOUND)

    def handleStreamStatus(self, status):
        if status.terminateState.isProcessing():
            self.cancelButton.setEnabled(False)
            self.cancelButton.setText(T("stopping", ellipsis=True))
        elif status.isPreparing():
            self.status.setText(T("preparing", ellipsis=True))
        else:
            self.status.setText(T("live-downloading", ellipsis=True))

    def handleVideoStatus(self, status):
        if status.isWaitingSkipped():
            self.skipWaitingButton.hide()
        if status.isDownloadSkipped():
            self.skipDownloadButton.setEnabled(False)
            self.pauseButton.setEnabled(False)
        if status.terminateState.isProcessing():
            self.skipWaitingButton.hide()
            self.skipDownloadButton.setEnabled(False)
            self.pauseButton.setEnabled(False)
            self.cancelButton.setEnabled(False)
            self.cancelButton.setText(T("canceling", ellipsis=True))
        elif status.isPreparing():
            self.status.setText(T("preparing", ellipsis=True))
        elif not status.pauseState.isFalse():
            self.skipWaitingButton.hide()
            self.skipDownloadButton.hide()
            if status.pauseState.isProcessing():
                self.pauseButton.setEnabled(False)
                self.cancelButton.setEnabled(False)
                self.pauseButton.setText(T("pausing", ellipsis=True))
            else:
                self.status.setText(T("paused"))
                self.pauseButton.setEnabled(True)
                self.cancelButton.setEnabled(True)
                self.pauseButton.setText(T("resume"))
        elif status.isWaiting():
            self.status.setText(f"{T('#Waiting for download')}: {status.getWaitingTime()}")
            self.skipWaitingButton.show()
            self.skipDownloadButton.show()
            self.downloadProgressBar.setRange(0, 0)
            self.pauseButton.hide()
        elif status.isUpdating():
            self.status.setText(T("#Checking for additional files", ellipsis=True))
            self.skipWaitingButton.hide()
            self.skipDownloadButton.show()
            self.pauseButton.hide()
        elif status.isEncoding():
            self.status.setText(f"{T('encoding', ellipsis=True)} ({T('download-skipped')})" if status.isDownloadSkipped() else T("encoding", ellipsis=True))
            self.skipWaitingButton.hide()
            self.skipDownloadButton.hide()
            self.downloadProgressBar.setRange(0, 100)
            self.pauseButton.hide()
        else:
            self.status.setText(T("downloading-updated-files" if status.isUpdateFound() else "downloading", ellipsis=True))
            self.skipWaitingButton.hide()
            self.skipDownloadButton.show()
            self.downloadProgressBar.setRange(0, 100)
            self.pauseButton.show()

    def handleClipStatus(self, status):
        if status.terminateState.isProcessing():
            self.cancelButton.setEnabled(False)
            self.cancelButton.setText(T("canceling", ellipsis=True))
        elif status.isPreparing():
            self.status.setText(T("preparing", ellipsis=True))
        else:
            self.status.setText(T("downloading", ellipsis=True))

    def handleStreamProgress(self, progress):
        duration = Utils.formatTime(*Utils.toTime(progress.seconds))
        self.duration.setText(duration)
        self.currentDuration.setText(duration)
        self.currentSize.setText(progress.size)

    def handleVideoProgress(self, progress):
        self.downloadProgressBar.setValue(progress.fileProgress)
        self.encodingProgressBar.setValue(progress.timeProgress)
        self.currentDuration.setText(f"{Utils.formatTime(*Utils.toTime(progress.seconds))} / {Utils.formatTime(*Utils.toTime(progress.totalSeconds))}")
        if progress.missingFiles != 0:
            self.dataLoss.show()
            self.dataLoss.setText(T("#Missing {missingFiles} segments ({missingSeconds})", missingFiles=progress.missingFiles, missingSeconds=Utils.formatTime(*Utils.toTime(progress.missingSeconds))))
        self.currentSize.setText(progress.size)

    def handleClipProgress(self, progress):
        self.downloadProgressBar.setValue(progress.byteSizeProgress)
        self.currentSize.setText(progress.size)

    def handleVideoDataUpdate(self, data):
        playlist = data.get("playlist")
        if playlist != None:
            start, end = playlist.timeRange.timeFrom, playlist.timeRange.timeTo
            totalSeconds = playlist.original.totalSeconds
            durationSeconds = playlist.totalSeconds
            self.showVideoDuration(start, end, totalSeconds, durationSeconds)

    def showVideoDuration(self, start, end, totalSeconds, durationSeconds):
        if start == None and end == None:
            self.duration.setText(Utils.formatTime(*Utils.toTime(totalSeconds)))
        else:
            self.duration.setText(T(
                "#{duration} - Crop: {totalDuration}({startTime}~{endTime})",
                duration=Utils.formatTime(*Utils.toTime(durationSeconds)),
                totalDuration=Utils.formatTime(*Utils.toTime(totalSeconds)),
                startTime="" if start == None else Utils.formatTime(*Utils.toTime(start)),
                endTime="" if end == None else Utils.formatTime(*Utils.toTime(end))
            ))

    def handleDownloadResult(self):
        if self.downloader.status.terminateState.isTrue():
            if self.downloader.status.getError() == None:
                if self.downloadInfo.type.isStream():
                    self.status.setText(T("download-stopped"))
                    self.openFileButton.show()
                else:
                    self.status.setText(T("download-canceled"))
                    self.currentSize.setText(Utils.formatByteSize(0))
            else:
                self.status.setText(T("download-aborted"))
        else:
            self.status.setText(f"{T('download-complete')} ({T('download-skipped')})" if self.downloader.status.isDownloadSkipped() else T("download-complete"))
            self.openFileButton.show()
        self.downloadProgressBar.setRange(0, 100)
        self.encodingProgressBar.setRange(0, 100)
        self.downloadProgressBar.setValue(100)
        self.encodingProgressBar.setValue(100)
        self.skipWaitingButton.hide()
        self.skipDownloadButton.hide()
        self.pauseButton.hide()
        self.cancelButton.hide()
        self.openLogsButton.show()

    def openLogs(self):
        try:
            Utils.openFile(self.downloader.logger.getPath())
        except:
            self.info(*Messages.INFO.FILE_NOT_FOUND)