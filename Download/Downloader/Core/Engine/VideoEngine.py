from .Config import Config
from .Playlist.PlaylistEngine import PlaylistEngine
from .Playlist.SegmentDownloader import SegmentDownloader
from .Playlist.MutableSegmentDownloader import MutableSegmentDownloader

from Core import App
from Core.GlobalExceptions import Exceptions
from Services.Utils.Utils import Utils
from Services.Logging.Logger import Logger
from Services.Playlist.Segment import Segment
from Download.DownloadInfo import DownloadInfo
from Download.Downloader.Core.Engine import Modules

from PyQt6 import QtCore


class VideoEngine(PlaylistEngine):
    def __init__(self, downloadInfo: DownloadInfo, status: Modules.Status, progress: Modules.Progress, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(downloadInfo, status, progress, logger, parent=parent)
        self._playlistManager.setRange(*self.downloadInfo.getCropRangeMilliseconds())
        self._refreshTimer.setInterval(Config.UPDATE_TRACK_INTERVAL)
        self._pausedSegments: list[Segment] = []

    def _updatePlaylist(self) -> None:
        self.status.setNextUpdateDateTime(None)
        self._syncStatus()
        super()._updatePlaylist()

    def _playlistUpdated(self) -> None:
        if self.status.terminateState.isFalse() and self.status.pauseState.isFalse():
            self.downloadInfo.content.lengthSeconds = self._playlistManager.playlist.totalSeconds
            self.downloadInfo.setCropRangeMilliseconds(*self._playlistManager.getSegmentRange())
            if self.downloadInfo.isUpdateTrackEnabled():
                if self._playlistManager.hasNewSegments() or self.status.getWaitingCount() < self.status.getMaxWaitingCount():
                    self.status.setNextUpdateDateTime(QtCore.QDateTime.currentDateTimeUtc().addMSecs(Config.UPDATE_TRACK_INTERVAL))
                    if self._playlistManager.hasNewSegments():
                        self.status.setWaitingCount(0)
                    else:
                        self.status.setWaitingCount(self.status.getWaitingCount() + 1)
                    self._playlistManager.playlist.setEndList(False)
                else:
                    self.status.setWaitingCount(-1)
                self._syncStatus()
            super()._playlistUpdated()

    def _createSegmentDownloader(self, segment: Segment) -> SegmentDownloader:
        return (MutableSegmentDownloader if self.downloadInfo.isUnmuteVideoEnabled() else SegmentDownloader)(
            self._networkAccessManager,
            segment,
            Utils.joinPath(self._safeTempDirectory.path(), f"{segment.sequence}.ts"),
            priority=self.downloadInfo.getPriority(),
            parent=self
        )

    def _segmentDownloadFinished(self, segmentDownloader: SegmentDownloader) -> None:
        if self.status.pauseState.isProcessing():
            while len(self._segmentDownloaders) > 0 and self._segmentDownloaders[0].isFinished():
                nextSegmentDownloader = self._segmentDownloaders.pop(0)
                nextSegmentDownloader.file.remove()
                nextSegmentDownloader.setParent(None)
            if len(self._segmentDownloaders) == 0:
                self.status.pauseState.setTrue()
                self._syncStatus()
        else:
            super()._segmentDownloadFinished(segmentDownloader)

    def _mergeSegment(self, segmentDownloader: SegmentDownloader) -> None:
        if isinstance(segmentDownloader, MutableSegmentDownloader):
            if segmentDownloader.isMuted():
                self.logger.warning(f"Failed to unmute segment: <Sequence: {segmentDownloader.segment.sequence} / Length: {segmentDownloader.segment.totalMilliseconds}>\n{segmentDownloader.segment.url.toString()}")
                self.progress.mutedFiles += 1
                self.progress.mutedMilliseconds += segmentDownloader.segment.totalMilliseconds
                self._syncProgress()
        super()._mergeSegment(segmentDownloader)

    def pause(self) -> None:
        if not self.status.pauseState.isTrue():
            self.logger.info("Pause Requested")
            self.status.pauseState.setProcessing()
            self.status.setNextUpdateDateTime(None)
            self.status.setWaitingCount(0)
            self._syncStatus()
            if self._refreshTimer.isActive():
                self._refreshTimer.stop()
            self._pausedSegments = [segmentDownloader.segment for segmentDownloader in self._segmentDownloaders]
            if len(self._segmentDownloaders) == 0:
                self.status.pauseState.setTrue()
                self._syncStatus()
            else:
                App.FileDownloadManager.cancelDownloads(self._segmentDownloaders)

    def resume(self) -> None:
        if self.status.pauseState.isTrue():
            self.logger.info("Resume Requested")
            self.status.pauseState.setFalse()
            self._syncStatus()
            self._downloadSegments(self._pausedSegments)
            self._pausedSegments.clear()
            self._updatePlaylist()

    def _isFileRemoveRequired(self) -> bool:
        return super()._isFileRemoveRequired() or (not self.status.terminateState.isFalse() and isinstance(self.status.getError(), Exceptions.AbortRequested))