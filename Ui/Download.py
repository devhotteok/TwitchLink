from Core.Ui import *
from Services.Messages import Messages
from Download.Downloader.Engine.Config import Config as EngineConfig
from Download.DownloadManager import DownloadManager


class Download(QtWidgets.QWidget, UiFile.download):
    def __init__(self, downloaderId):
        super().__init__()
        self.downloader = DownloadManager.get(downloaderId)
        self.downloadInfo = self.downloader.setup.downloadInfo
        self.videoData = self.downloadInfo.videoData
        self.setWindowTitle(self.videoData.title)
        self.window_title.setText(self.videoData.title)
        self.categoryImageLoader = Utils.ImageLoader(self.category_image, self.videoData.game.boxArtURL, Config.CATEGORY_IMAGE)
        self.category.setText(self.videoData.game.displayName)
        self.title.setText(self.videoData.title)
        self.thumbnail_image.setImageSizePolicy((480, 270), (1920, 1080))
        if self.downloadInfo.type.isStream():
            self.thumbnailImageLoader = Utils.ImageLoader(self.thumbnail_image, self.videoData.previewImageURL, Config.THUMBNAIL_IMAGE)
            self.user_name.setText(self.videoData.broadcaster.displayName)
            self.date.setText(self.videoData.createdAt.toUTC(DB.localization.getTimezone()))
            self.duration.setText(T("unknown"))
            self.view_countInfo.setText(T("#Viewer Count:"))
            self.view_count.setText(self.videoData.viewersCount)
            self.downloadProgressBar.setRange(0, 0)
            self.encodingProgressBar.setRange(0, 0)
            self.pauseButton.hide()
            self.cancelButton.setText(T("stop"))
        else:
            self.liveLabelArea.hide()
            self.thumbnailImageLoader = Utils.ImageLoader(self.thumbnail_image, self.videoData.previewThumbnailURL, Config.THUMBNAIL_IMAGE)
            self.user_name.setText(self.videoData.owner.displayName)
            self.date.setText(self.videoData.publishedAt.toUTC(DB.localization.getTimezone()))
            start, end = self.downloadInfo.range
            totalSeconds = self.videoData.lengthSeconds.totalSeconds()
            durationSeconds = (end or totalSeconds) - (start or 0)
            self.showVideoDuration(start, end, totalSeconds, durationSeconds)
            self.view_countInfo.setText(T("#View Count:"))
            self.view_count.setText(self.videoData.viewCount)
            self.skipWaitingButton.clicked.connect(self.skipWaiting)
            self.forceEncodingButton.clicked.connect(self.forceEncoding)
            self.pauseButton.clicked.connect(self.pauseResume)
            self.cancelButton.setText(T("cancel"))
        self.resolution.setText(self.downloadInfo.resolution)
        self.file.setText(self.downloadInfo.getAbsoluteFileName())
        sizePolicy = self.skipWaitingButton.sizePolicy()
        sizePolicy.setRetainSizeWhenHidden(True)
        self.skipWaitingButton.setSizePolicy(sizePolicy)
        self.forceEncodingButton.setSizePolicy(sizePolicy)
        self.skipWaitingButton.hide()
        self.forceEncodingButton.hide()
        self.cancelButton.clicked.connect(self.cancel)
        self.openFolderButton.clicked.connect(self.openFolder)
        self.openFileButton.clicked.connect(self.openFile)
        self.openFileButton.hide()
        self.connectDownloader()

    def connectDownloader(self):
        if self.downloadInfo.type.isStream():
            self.downloader.statusUpdate.connect(self.handleStreamStatus)
            self.downloader.progressUpdate.connect(self.handleStreamProgress)
            self.downloader.finished.connect(self.handleDownloadResult)
            self.handleStreamProgress(self.downloader.progress)
            self.handleStreamStatus(self.downloader.status)
        else:
            self.downloader.statusUpdate.connect(self.handleVideoStatus)
            self.downloader.progressUpdate.connect(self.handleVideoProgress)
            self.downloader.dataUpdate.connect(self.handleVideoDataUpdate)
            self.downloader.finished.connect(self.handleDownloadResult)
            self.handleVideoStatus(self.downloader.status)
            self.handleVideoProgress(self.downloader.progress)

    def disconnectDownloader(self):
        if self.downloadInfo.type.isStream():
            self.downloader.statusUpdate.disconnect(self.handleStreamStatus)
            self.downloader.progressUpdate.disconnect(self.handleStreamProgress)
        else:
            self.downloader.statusUpdate.disconnect(self.handleVideoStatus)
            self.downloader.progressUpdate.disconnect(self.handleVideoProgress)
            self.downloader.dataUpdate.disconnect(self.handleVideoDataUpdate)
        self.downloader.finished.disconnect(self.handleDownloadResult)

    def skipWaiting(self):
        self.downloader.skipWaiting()

    def forceEncoding(self):
        self.downloader.skipDownload()

    def pauseResume(self):
        if self.downloader.status.pauseState.isFalse():
            self.downloader.pause()
        else:
            self.downloader.resume()
            self.pauseButton.setText(T("pause"))

    def cancel(self):
        if Utils.ask(*(Messages.ASK.STOP_DOWNLOAD if self.downloadInfo.type.isStream() else Messages.ASK.CANCEL_DOWNLOAD)):
            self.downloader.cancel()
            if self.downloader.status.terminateState.isFalse():
                Utils.info(*Messages.INFO.DOWNLOAD_ALREADY_COMPLETED)

    def openFolder(self):
        try:
            Utils.openFolder(self.downloadInfo.directory)
        except:
            Utils.info(*Messages.INFO.FOLDER_NOT_FOUND)

    def openFile(self):
        try:
            Utils.openFile(self.downloadInfo.getAbsoluteFileName())
        except:
            Utils.info(*Messages.INFO.FILE_NOT_FOUND)

    def handleStreamStatus(self, status):
        if status.terminateState.isProcessing():
            self.cancelButton.setEnabled(False)
            self.cancelButton.setText(T("stopping", ellipsis=True))
        elif status.isPreparing():
            self.status.setText(T("preparing", ellipsis=True))
        else:
            self.status.setText(T("downloading-live-stream", ellipsis=True))

    def handleVideoStatus(self, status):
        if status.terminateState.isProcessing():
            self.pauseButton.setEnabled(False)
            self.cancelButton.setEnabled(False)
            self.cancelButton.setText(T("canceling", ellipsis=True))
        elif status.isPreparing():
            self.status.setText(T("preparing", ellipsis=True))
        elif not status.pauseState.isFalse() and not status.isDownloadSkipped():
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
            self.status.setText(
                "{} : {}".format(
                    T("#Waiting for download"),
                    status.getWaitingTime()
                )
            )
            self.skipWaitingButton.show()
            self.downloadProgressBar.setRange(0, 0)
            self.pauseButton.hide()
        elif status.isUpdating():
            self.status.setText(T("#Checking for additional files", ellipsis=True))
            self.skipWaitingButton.hide()
            self.pauseButton.hide()
        elif status.isEncoding():
            self.status.setText(T("forced-encoding" if status.isDownloadSkipped() else "encoding", ellipsis=True))
            self.skipWaitingButton.hide()
            self.forceEncodingButton.hide()
            self.downloadProgressBar.setRange(0, 100)
            self.pauseButton.hide()
        else:
            self.status.setText(T("downloading-updated-files" if status.isUpdateFound() else "downloading", ellipsis=True))
            self.skipWaitingButton.hide()
            self.downloadProgressBar.setRange(0, 100)
            self.pauseButton.show()
            if status.isDownloadSkipped():
                self.forceEncodingButton.setEnabled(False)

    def handleStreamProgress(self, progress):
        self.currentDuration.setText(Utils.formatTime(*Utils.toTime(progress.seconds)))
        self.currentSize.setText(progress.size)

    def handleVideoProgress(self, progress):
        self.downloadProgressBar.setValue(progress.fileProgress)
        self.encodingProgressBar.setValue(progress.timeProgress)
        self.currentDuration.setText("{time} / {totalTime}".format(time=Utils.formatTime(*Utils.toTime(progress.seconds)), totalTime=Utils.formatTime(*Utils.toTime(progress.totalSeconds))))
        self.currentSize.setText(progress.size)
        self.checkDownloadSkipEnabled()

    def checkDownloadSkipEnabled(self):
        status = self.downloader.status
        if status.isDownloading() or status.isWaiting() or status.isUpdating():
            if self.downloader.progress.fileProgress < EngineConfig.SKIP_DOWNLOAD_ENABLE_POINT:
                self.forceEncodingButton.hide()
            else:
                self.forceEncodingButton.show()

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
                "#{duration} - Crop : {totalDuration}({startTime}~{endTime})",
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
            else:
                self.status.setText(T("download-aborted"))
        else:
            self.status.setText(T("download-complete"))
            self.openFileButton.show()
        self.downloadProgressBar.setRange(0, 100)
        self.encodingProgressBar.setRange(0, 100)
        self.downloadProgressBar.setValue(100)
        self.encodingProgressBar.setValue(100)
        self.pauseButton.hide()
        self.cancelButton.setText(T("complete"))
        self.cancelButton.clicked.disconnect()
        self.cancelButton.clicked.connect(self.close)
        self.cancelButton.setEnabled(True)

    def closeEvent(self, event):
        self.disconnectDownloader()
        return super().closeEvent(event)