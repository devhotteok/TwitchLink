from Core.Ui import *
from Services.Messages import Messages
from Search import ExternalPlaylist
from Download.DownloadHistoryManager import DownloadHistoryManager
from Ui.Components.Widgets.RetryDownloadButton import RetryDownloadButton


class DownloadHistoryView(QtWidgets.QWidget, UiFile.downloadHistoryView):
    def __init__(self, downloadHistory, parent=None):
        super(DownloadHistoryView, self).__init__(parent=parent)
        self.downloadHistory = downloadHistory
        self.downloadInfo = downloadHistory.downloadInfo
        self.videoData = self.downloadInfo.videoData
        self.categoryImage.loadImage(filePath=Images.CATEGORY_IMAGE, url=self.videoData.game.boxArtURL, urlFormatSize=ImageSize.CATEGORY)
        self.category.setText(self.videoData.game.displayName)
        self.title.setText(self.videoData.title)
        if self.downloadInfo.type.isStream():
            self.showVideoType("stream" if self.videoData.isLive() else "rerun")
            self.thumbnailImage.loadImage(filePath=Images.PREVIEW_IMAGE, url=self.videoData.previewImageURL, urlFormatSize=ImageSize.STREAM_PREVIEW, refresh=True)
            self.channel.setText(self.videoData.broadcaster.displayName)
            self.date.setText(self.videoData.createdAt.toTimeZone(DB.localization.getTimezone()))
            self.duration.setText(T("unknown"))
            self.unmuteVideoTag.hide()
            self.updateTrackTag.hide()
            self.optimizeFileTag.setVisible(self.downloadInfo.isOptimizeFileEnabled())
            self.prioritizeTag.hide()
        elif self.downloadInfo.type.isVideo():
            self.showVideoType("video")
            self.thumbnailImage.loadImage(filePath=Images.THUMBNAIL_IMAGE, url=self.videoData.previewThumbnailURL, urlFormatSize=ImageSize.VIDEO_THUMBNAIL)
            self.channel.setText(self.videoData.owner.displayName)
            self.date.setText(self.videoData.publishedAt.toTimeZone(DB.localization.getTimezone()))
            start, end = self.downloadInfo.range
            totalSeconds = self.videoData.lengthSeconds
            durationSeconds = (end or totalSeconds) - (start or 0)
            self.showVideoDuration(start, end, totalSeconds, durationSeconds)
            self.unmuteVideoTag.setVisible(self.downloadInfo.isUnmuteVideoEnabled())
            self.updateTrackTag.setVisible(self.downloadInfo.isUpdateTrackEnabled())
            self.optimizeFileTag.setVisible(self.downloadInfo.isOptimizeFileEnabled())
            self.prioritizeTag.setVisible(self.downloadInfo.isPrioritizeEnabled())
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
        self.resolution.setText(self.downloadInfo.resolution.displayName)
        self.file.setText(self.downloadInfo.getAbsoluteFileName())
        self.retryButtonManager = RetryDownloadButton(self.downloadInfo, self.retryButton, parent=self)
        self.accountPageShowRequested = self.retryButtonManager.accountPageShowRequested
        self.openFolderButton.clicked.connect(self.openFolder)
        self.openFileButton.clicked.connect(self.openFile)
        self.openLogsButton.clicked.connect(self.openLogs)
        self.deleteButton.clicked.connect(self.deleteHistory)
        self.downloadHistory.historyChanged.connect(self.reloadHistoryData)
        self.reloadHistoryData()

    def reloadHistoryData(self):
        self.startedAt.setText(self.downloadHistory.startedAt.toTimeZone(DB.localization.getTimezone()))
        self.completedAt.setText(T("unknown") if self.downloadHistory.completedAt == None else self.downloadHistory.completedAt.toTimeZone(DB.localization.getTimezone()))
        self.result.setText(T(self.downloadHistory.result))
        if self.downloadHistory.result == self.downloadHistory.Result.completed or self.downloadHistory.result == self.downloadHistory.Result.skipped or self.downloadHistory.result == self.downloadHistory.Result.stopped:
            self.setCursor(QtCore.Qt.PointingHandCursor)
            self.openFileButton.setEnabled(True)
            self.openFileButton.setIcon(QtGui.QIcon(Icons.FILE_ICON))
            self.openLogsButton.setEnabled(True)
            self.openLogsButton.setIcon(QtGui.QIcon(Icons.TEXT_FILE_ICON))
        else:
            self.setCursor(QtCore.Qt.ArrowCursor)
            self.openFileButton.setEnabled(False)
            if self.downloadHistory.result == self.downloadHistory.Result.downloading:
                self.openFileButton.setIcon(QtGui.QIcon(Icons.DOWNLOADING_FILE_ICON))
                self.openLogsButton.setEnabled(False)
                self.openLogsButton.setIcon(QtGui.QIcon(Icons.GENERATING_FILE_ICON))
            else:
                styleSheet = "QLabel {color: #ff0000;}"
                self.channel.setStyleSheet(styleSheet)
                self.videoArea.setStyleSheet(styleSheet)
                self.openFileButton.setIcon(QtGui.QIcon(Icons.FILE_NOT_FOUND_ICON))
                self.openLogsButton.setEnabled(True)
                self.openLogsButton.setIcon(QtGui.QIcon(Icons.TEXT_FILE_ICON))

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

    def openLogs(self):
        try:
            Utils.openFile(self.downloadHistory.logFile)
        except:
            self.info(*Messages.INFO.FILE_NOT_FOUND)

    def deleteHistory(self):
        DownloadHistoryManager.removeHistory(self.downloadHistory)

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
                startTime="" if start == None else Utils.formatTime(*Utils.toTime(start / 1000)),
                endTime="" if end == None else Utils.formatTime(*Utils.toTime(end / 1000))
            ))