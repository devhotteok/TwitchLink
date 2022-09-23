from Core.Ui import *
from Services.Messages import Messages
from Search import ExternalPlaylist
from Download.Downloader.Engine.Config import Config as DownloadEngineConfig
from Download.DownloadManager import DownloadManager
from Ui.Components.Widgets.RetryDownloadButton import RetryDownloadButton


class DownloaderControl:
    def __init__(self):
        self._removeEnabled = False
        self._removeRegistered = False

    def enableRemove(self):
        self._removeEnabled = True

    def isRemoveEnabled(self):
        return self._removeEnabled

    def registerRemove(self):
        self._removeRegistered = True

    def isRemoveRegistered(self):
        return self._removeRegistered


class DownloadPreview(QtWidgets.QWidget, UiFile.downloadPreview):
    resizedSignal = QtCore.pyqtSignal()

    def __init__(self, downloaderId, parent=None):
        super(DownloadPreview, self).__init__(parent=parent)
        self.downloaderId = downloaderId
        self.downloader = DownloadManager.get(self.downloaderId)
        self.control = DownloaderControl()
        self.downloadInfo = self.downloader.setup.downloadInfo
        self.videoData = self.downloadInfo.videoData
        self.categoryImage.loadImage(filePath=Images.CATEGORY_IMAGE, url=self.videoData.game.boxArtURL, urlFormatSize=ImageSize.CATEGORY)
        self.category.setText(self.videoData.game.displayName)
        self.title.setText(self.videoData.title)
        if self.downloadInfo.type.isStream():
            self.showVideoType("stream" if self.videoData.isLive() else "rerun")
            self.thumbnailImage.loadImage(filePath=Images.PREVIEW_IMAGE, url=self.videoData.previewImageURL, urlFormatSize=ImageSize.STREAM_PREVIEW, refresh=True)
            self.channel.setText(self.videoData.broadcaster.displayName)
            self.date.setText(self.videoData.createdAt.toTimeZone(DB.localization.getTimezone()))
            self.unmuteVideoTag.hide()
            self.updateTrackTag.hide()
            self.optimizeFileTag.setVisible(self.downloadInfo.isOptimizeFileEnabled())
            self.prioritizeTag.hide()
            self.progressBar.setRange(0, 0)
            self.pauseButton.hide()
            self.cancelButton.setText(T("stop"))
        elif self.downloadInfo.type.isVideo():
            self.showVideoType("video")
            self.thumbnailImage.loadImage(filePath=Images.THUMBNAIL_IMAGE, url=self.videoData.previewThumbnailURL, urlFormatSize=ImageSize.VIDEO_THUMBNAIL)
            self.channel.setText(self.videoData.owner.displayName)
            self.date.setText(self.videoData.publishedAt.toTimeZone(DB.localization.getTimezone()))
            start, end = self.downloadInfo.getRangeInSeconds()
            totalSeconds = self.videoData.lengthSeconds
            durationSeconds = (end or totalSeconds) - (start or 0)
            self.showVideoDuration(start, end, totalSeconds, durationSeconds)
            self.unmuteVideoTag.setVisible(self.downloadInfo.isUnmuteVideoEnabled())
            self.updateTrackTag.setVisible(self.downloadInfo.isUpdateTrackEnabled())
            self.optimizeFileTag.setVisible(self.downloadInfo.isOptimizeFileEnabled())
            self.prioritizeTag.setVisible(self.downloadInfo.isPrioritizeEnabled())
            self.pauseButton.clicked.connect(self.pauseResume)
            self.cancelButton.setText(T("cancel"))
        else:
            self.showVideoType("clip")
            self.thumbnailImage.loadImage(filePath=Images.THUMBNAIL_IMAGE, url=self.videoData.thumbnailURL, urlFormatSize=ImageSize.CLIP_THUMBNAIL)
            self.channel.setText(self.videoData.broadcaster.displayName)
            self.date.setText(self.videoData.createdAt.toTimeZone(DB.localization.getTimezone()))
            self.duration.setText(self.videoData.durationString)
            self.unmuteVideoTag.hide()
            self.updateTrackTag.hide()
            self.optimizeFileTag.hide()
            self.prioritizeTag.setVisible(self.downloadInfo.isPrioritizeEnabled())
            self.pauseButton.hide()
            self.cancelButton.setText(T("cancel"))
        self.resolution.setText(self.downloadInfo.resolution.displayName)
        self.file.setText(self.downloadInfo.getAbsoluteFileName())
        self.retryButtonManager = RetryDownloadButton(self.downloadInfo, self.retryButton, self.downloader.getId(), parent=self)
        self.accountPageShowRequested = self.retryButtonManager.accountPageShowRequested
        self.retryButton.hide()
        self.openFolderButton.clicked.connect(self.openFolder)
        self.openFileButton.clicked.connect(self.openFile)
        self.setOpenFileButton(downloadingFile=True)
        self.closeButton.clicked.connect(self.tryRemoveDownloader)
        self.alertIcon = Utils.setSvgIcon(self.alertIcon, Icons.ALERT_RED_ICON)
        self.alertIcon.hide()
        self.cancelButton.clicked.connect(self.cancel)
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
            if hasattr(self.downloader, "playlistManager"):
                self.handleVideoDataUpdate({"playlistManager": self.downloader.playlistManager})
        else:
            self.downloader.statusUpdate.connect(self.handleClipStatus)
            self.downloader.progressUpdate.connect(self.handleClipProgress)
            self.handleClipStatus(self.downloader.status)
            self.handleClipProgress(self.downloader.progress)

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

    def tryRemoveDownloader(self):
        if self.control.isRemoveEnabled():
            self.removeDownloader()
        else:
            if self.downloader.status.terminateState.isFalse():
                if self.ask(*(Messages.ASK.STOP_DOWNLOAD if self.downloadInfo.type.isStream() else Messages.ASK.CANCEL_DOWNLOAD)):
                    self.downloader.cancel()
                else:
                    return
            if self.control.isRemoveEnabled():
                self.removeDownloader()
            else:
                self.setEnabled(False)
                self.control.registerRemove()

    def removeDownloader(self):
        DownloadManager.remove(self.downloaderId)

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

    def handleStreamStatus(self, status):
        if status.terminateState.isProcessing():
            self.cancelButton.setEnabled(False)
            self.cancelButton.setText(T("stopping", ellipsis=True))
        elif status.isPreparing():
            self.status.setText(T("preparing", ellipsis=True))
        else:
            self.status.setText(T("live-downloading", ellipsis=True))

    def handleVideoStatus(self, status):
        if status.isDownloadSkipped():
            self.pauseButton.setEnabled(False)
        if status.terminateState.isProcessing():
            self.pauseButton.setEnabled(False)
            self.cancelButton.setEnabled(False)
            self.cancelButton.setText(T("canceling", ellipsis=True))
        elif status.isPreparing():
            self.status.setText(T("preparing", ellipsis=True))
        elif not status.pauseState.isFalse():
            if status.pauseState.isProcessing():
                self.pauseButton.setEnabled(False)
                self.pauseButton.setText(T("pausing", ellipsis=True))
            else:
                self.status.setText(T("paused"))
                self.pauseButton.setEnabled(True)
                self.pauseButton.setText(T("resume"))
        elif status.isWaiting():
            self.status.setText(f"{T('#Waiting for download')}({status.getWaitingCount()}/{status.getMaxWaitingCount()}): {status.getWaitingTime()}")
            self.progressBar.setRange(0, 0)
            self.pauseButton.hide()
        elif status.isUpdating():
            self.status.setText(T("#Checking for additional files", ellipsis=True))
            self.pauseButton.hide()
        elif status.isEncoding():
            encodingString = T("encoding", ellipsis=True)
            if self.downloadInfo.isOptimizeFileEnabled():
                encodingString = f"{encodingString} [{T('optimize-file')}]"
            self.status.setText(f"{encodingString} ({T('download-skipped')})" if status.isDownloadSkipped() else encodingString)
            self.progressBar.setRange(0, 100)
            self.progressBar.setValue(self.downloader.progress.timeProgress)
            self.pauseButton.hide()
        else:
            self.status.setText(T("downloading-updated-files" if status.isUpdateFound() else "downloading", ellipsis=True))
            self.progressBar.setRange(0, 100)
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
        self.duration.setText(Utils.formatTime(*Utils.toTime(progress.seconds)))

    def handleVideoProgress(self, progress):
        self.progressBar.setValue(progress.timeProgress if self.downloader.status.isEncoding() else progress.fileProgress)

    def handleClipProgress(self, progress):
        self.progressBar.setValue(progress.sizeProgress)

    def handleVideoDataUpdate(self, data):
        playlistManager = data.get("playlistManager")
        if playlistManager != None:
            startMilliseconds, endMilliseconds = playlistManager.getTimeRange()
            start = None if startMilliseconds == None else startMilliseconds / 1000
            end = None if endMilliseconds == None else endMilliseconds / 1000
            totalSeconds = playlistManager.original.totalSeconds
            durationSeconds = playlistManager.totalSeconds
            self.showVideoDuration(start, end, totalSeconds, durationSeconds)

    def showVideoType(self, videoType):
        self.videoTypeLabel.setText(f"{T('external-content')}:{T(videoType)}" if isinstance(self.downloadInfo.accessToken, ExternalPlaylist.ExternalPlaylist) else T(videoType))

    def showVideoDuration(self, start, end, totalSeconds, durationSeconds):
        if start == None and end == None:
            self.duration.setText(Utils.formatTime(*Utils.toTime(totalSeconds)))
        else:
            self.duration.setText(T(
                "#{duration} [Original: {totalDuration} / Crop: {startTime}~{endTime}]",
                duration=Utils.formatTime(*Utils.toTime(durationSeconds)),
                totalDuration=Utils.formatTime(*Utils.toTime(totalSeconds)),
                startTime="" if start == None else Utils.formatTime(*Utils.toTime(start)),
                endTime="" if end == None else Utils.formatTime(*Utils.toTime(end))
            ))

    def handleDownloadResult(self):
        if self.downloader.status.terminateState.isTrue():
            if self.downloader.status.getError() == None:
                if self.downloadInfo.type.isStream():
                    self.setOpenFileButton(openFile=True)
                    self.statusArea.hide()
                else:
                    self.retryButton.show()
                    self.setOpenFileButton(fileNotFound=True)
                    self.status.setText(T("download-canceled"))
                    self.alertIcon.show()
                    self.progressBar.showWarning()
            else:
                self.retryButton.show()
                self.setOpenFileButton(fileNotFound=True)
                self.status.setText(T("download-aborted"))
                self.alertIcon.show()
                self.progressBar.showError()
        else:
            self.setOpenFileButton(openFile=True)
            self.statusArea.hide()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(100)
        self.buttonArea.hide()
        self.updateGeometry()
        self.resizedSignal.emit()

    def needStatsUpdate(self):
        if self.downloader.status.terminateState.isTrue():
            if self.downloader.status.getError() == None:
                if self.downloadInfo.type.isStream():
                    return True
            return False
        else:
            return True

    def processCompleteEvent(self):
        if self.needStatsUpdate():
            DB.temp.updateDownloadStats(self.downloader.progress.totalByteSize)
            downloadStats = DB.temp.getDownloadStats()
            if downloadStats["totalFiles"] < DownloadEngineConfig.SHOW_STATS[0]:
                showContributeInfo = downloadStats["totalFiles"] in DownloadEngineConfig.SHOW_STATS[1]
            else:
                showContributeInfo = downloadStats["totalFiles"] % DownloadEngineConfig.SHOW_STATS[0] == 0
        else:
            showContributeInfo = False
        self.control.enableRemove()
        if self.control.isRemoveRegistered():
            self.removeDownloader()
        if self.downloader.status.terminateState.isTrue():
            error = self.downloader.status.getError()
            if error != None:
                if error == Exceptions.FileSystemError:
                    self.info(*Messages.INFO.FILE_SYSTEM_ERROR)
                elif error == Exceptions.NetworkError:
                    self.info(*Messages.INFO.NETWORK_ERROR)
                else:
                    infoString = T("#An error occurred while downloading.")
                    if self.downloadInfo.type.isVideo():
                        if self.downloadInfo.isOptimizeFileEnabled():
                            advice = T("#If the error persists, try disabling the '{menuName}' option.", menuName=T("optimize-file"))
                            infoString = f"{infoString}\n\n{advice}"
                    self.info("error", infoString, contentTranslate=False)
        elif DB.general.isNotifyEnabled():
            fileName = self.downloader.setup.downloadInfo.getAbsoluteFileName()
            if self.ask(
                "download-complete",
                f"{T('#Download completed.')}\n\n{fileName}",
                contentTranslate=False,
                okText="open",
                cancelText="ok"
            ):
                try:
                    Utils.openFile(fileName)
                except:
                    self.info(*Messages.INFO.FILE_NOT_FOUND)
        if showContributeInfo:
            if self.ask("contribute", T("#You have downloaded a total of {totalFiles}({totalSize}) videos so far.\nPlease become a patron of {appName} for better functionality and service.", totalFiles=downloadStats["totalFiles"], totalSize=Utils.formatByteSize(downloadStats["totalByteSize"]), appName=Config.APP_NAME), contentTranslate=False, defaultOk=True):
                Utils.openUrl(Utils.joinUrl(Config.HOMEPAGE_URL, "donate", params={"lang": DB.localization.getLanguage()}))

    def setOpenFileButton(self, openFile=False, downloadingFile=False, fileNotFound=False):
        buttonText = T("open-file")
        if openFile:
            self.openFileButton.setEnabled(True)
            self.openFileButton.setIcon(QtGui.QIcon(Icons.FILE_ICON))
            self.openFileButton.setToolTip(buttonText)
        elif downloadingFile:
            self.openFileButton.setEnabled(False)
            self.openFileButton.setIcon(QtGui.QIcon(Icons.DOWNLOADING_FILE_ICON))
            self.openFileButton.setToolTip(f"{buttonText}({T('downloading', ellipsis=True)})")
        elif fileNotFound:
            self.openFileButton.setEnabled(False)
            self.openFileButton.setIcon(QtGui.QIcon(Icons.FILE_NOT_FOUND_ICON))
            self.openFileButton.setToolTip(f"{buttonText}({T('file-not-found')})")