from ..Config import Config
from ..BaseEngine import BaseEngine
from .SegmentDownloader import SegmentDownloader
from ..FFmpeg.FFmpeg import FFmpeg

from Core import App
from Core.GlobalExceptions import Exceptions
from Services.Utils.Utils import Utils
from Services.Logging.Logger import Logger
from Services.Temp.TempManager import SafeTempDirectory
from Services.Playlist import Playlist
from Services.Playlist.Segment import Segment
from Services.Playlist.PlaylistManager import PlaylistManager
from Download.DownloadInfo import DownloadInfo
from Download.Downloader.Core.Engine import Modules

from PyQt6 import QtCore

import re


class PlaylistEngine(BaseEngine):
    def __init__(self, downloadInfo: DownloadInfo, status: Modules.Status, progress: Modules.Progress, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(downloadInfo, status, progress, logger, parent=parent)
        self._playlistManager = PlaylistManager(self._networkAccessManager, self.downloadInfo.getUrl(), timeout=Config.PLAYLIST_REQUEST_TIMEOUT, maxRetryCount=Config.PLAYLIST_UPDATE_MAX_RETRY_COUNT, retryInterval=Config.PLAYLIST_UPDATE_RETRY_INTERVAL, parent=self)
        self._playlistManager.errorOccurred.connect(self._playlistManagerErrorOccurred)
        self._playlistManager.playlistUpdated.connect(self._playlistUpdated)
        self._safeTempDirectory: SafeTempDirectory | None = None
        self._FFmpeg: FFmpeg | None = None
        self._segmentDownloaders: list[SegmentDownloader] = []
        self._refreshTimer = QtCore.QTimer(parent=self)
        self._refreshTimer.setSingleShot(True)
        self._refreshTimer.setInterval(Config.PLAYLIST_UPDATE_INTERVAL)
        self._refreshTimer.timeout.connect(self._updatePlaylist)

    def start(self) -> None:
        super().start()
        self._safeTempDirectory = SafeTempDirectory(self.downloadInfo.directory, parent=self)
        if self._safeTempDirectory.getError() == None:
            self.logger.info(f"Using Temp Directory: {self._safeTempDirectory.path()}")
            if self.downloadInfo.isRemuxEnabled():
                self._startFFmpegProcess()
            else:
                self._updatePlaylist()
        else:
            self._raiseException(self._safeTempDirectory.getError())
            self._finish()

    def _finish(self) -> None:
        if self._safeTempDirectory.getError() == None:
            self._safeTempDirectory.clear()
        super()._finish()

    def _startFFmpegProcess(self) -> None:
        self._FFmpeg = FFmpeg(self.logger, parent=self)
        self._FFmpeg.started.connect(self._updatePlaylist)
        self._FFmpeg.finished.connect(self._FFmpegProcessFinished)
        self._FFmpeg.start(
            outputTarget=self.downloadInfo.getAbsoluteFileName(),
            transcode=False
        )

    def _FFmpegProcessFinished(self) -> None:
        exception = self._FFmpeg.getError()
        self._FFmpeg.deleteLater()
        self._FFmpeg = None
        if exception == None:
            self._checkDone()
        else:
            self._raiseException(exception)

    def _updatePlaylist(self) -> None:
        self._playlistManager.update()

    def _playlistManagerErrorOccurred(self, exception: Exceptions.AbortRequested | Exceptions.NetworkError | Playlist.Exceptions.InvalidPlaylist) -> None:
        self._raiseException(exception)

    def _playlistUpdated(self) -> None:
        if self.status.terminateState.isFalse():
            if self._playlistManager.hasNewSegments():
                segmentsToDownload = []
                for segment in self._playlistManager.getNewSegments():
                    self.progress.totalFiles += 1
                    self.progress.totalMilliseconds += segment.totalMilliseconds
                    if self.downloadInfo.type.isStream() and self.downloadInfo.isSkipAdsEnabled() and any(re.match(filter, segment.title) for filter in Config.STREAM_SEGMENT_TITLE_FILTER_REGEX):
                        self.progress.skippedFiles += 1
                        self.progress.skippedMilliseconds += segment.totalMilliseconds
                        self.logger.info(f"Skipping Segment: <Sequence: {segment.sequence} / Length: {segment.totalMilliseconds}>\n{segment.url.toString()}")
                    else:
                        segmentsToDownload.append(segment)
                self._downloadSegments(segmentsToDownload)
                self._syncProgress()
            if self._playlistManager.playlist.isEndList():
                self._checkDone()
            else:
                self._refreshTimer.start()

    def _downloadSegments(self, segments: list[Segment]) -> None:
        segmentDownloaders = []
        for segment in segments:
            segmentDownloader = self._createSegmentDownloader(segment)
            segmentDownloader.errorOccurred.connect(self._segmentDownloadFailed)
            segmentDownloader.finished.connect(self._segmentDownloadFinished)
            segmentDownloaders.append(segmentDownloader)
        App.FileDownloadManager.startDownloads(segmentDownloaders)
        self._segmentDownloaders.extend(segmentDownloaders)

    def _createSegmentDownloader(self, segment: Segment) -> SegmentDownloader:
        return SegmentDownloader(
            self._networkAccessManager,
            segment,
            Utils.joinPath(self._safeTempDirectory.path(), f"{segment.sequence}.ts"),
            priority=self.downloadInfo.getPriority(),
            parent=self
        )

    def _segmentDownloadFailed(self, segmentDownloader: SegmentDownloader) -> None:
        exception = segmentDownloader.getError()
        self.logger.warning(f"Segment Download Failed: <Sequence: {segmentDownloader.segment.sequence} / Length: {segmentDownloader.segment.totalMilliseconds}>\n{segmentDownloader.segment.url.toString()}")
        self.logger.exception(exception)
        if not isinstance(exception, Exceptions.AbortRequested):
            self.progress.missingFiles += 1
            self.progress.missingMilliseconds += segmentDownloader.segment.totalMilliseconds
            self._syncProgress()
            if isinstance(exception, Exceptions.FileSystemError):
                self._raiseException(exception)

    def _segmentDownloadFinished(self, segmentDownloader: SegmentDownloader) -> None:
        while len(self._segmentDownloaders) > 0 and self._segmentDownloaders[0].isFinished():
            nextSegmentDownloader = self._segmentDownloaders.pop(0)
            if nextSegmentDownloader.getError() == None and not self.status.terminateState.isProcessing():
                self._mergeSegment(nextSegmentDownloader)
            nextSegmentDownloader.file.remove()
            nextSegmentDownloader.setParent(None)
        self._checkDone()

    def _checkDone(self) -> None:
        if len(self._segmentDownloaders) == 0 and not self.status.isDone():
            if self.status.terminateState.isProcessing() or self._playlistManager.playlist.isEndList():
                if self._FFmpeg == None:
                    self._finish()
                elif self.status.terminateState.isProcessing():
                    self._FFmpeg.terminate()
                else:
                    self._FFmpeg.closeStream()

    def _mergeSegment(self, segmentDownloader: SegmentDownloader) -> None:
        if segmentDownloader.file.open(QtCore.QIODevice.OpenModeFlag.ReadOnly):
            while not segmentDownloader.file.atEnd():
                if self.downloadInfo.isRemuxEnabled():
                    if self._FFmpeg == None:
                        self.logger.warning("Unable to find pipe target.")
                        self._raiseException(Exceptions.UnexpectedError())
                    elif self._FFmpeg.write(segmentDownloader.file.read(Config.FILE_CHUNK_SIZE)) == -1 or not self._FFmpeg.waitForBytesWritten(Config.PIPE_TIMEOUT):
                        self.logger.warning("Unable to write data to pipe.")
                        self._raiseException(Exceptions.UnexpectedError())
                else:
                    if self.file.write(segmentDownloader.file.read(Config.FILE_CHUNK_SIZE)) == -1:
                        self.logger.warning("Unable to write data to file.")
                        self.file.close()
                        self._raiseException(Exceptions.FileSystemError(self.file))
            segmentDownloader.file.close()
            self.progress.files += 1
            self.progress.milliseconds += segmentDownloader.segment.totalMilliseconds
            self.progress.byteSize = self.file.size()
            self.progress.totalByteSize = self.progress.byteSize
            self._syncProgress()
        else:
            self._raiseException(Exceptions.FileSystemError(segmentDownloader.file))

    def _raiseException(self, exception: Exceptions.AbortRequested | Exceptions.FileSystemError | Exceptions.NetworkError | Exceptions.ProcessError | Exceptions.UnexpectedError) -> None:
        super()._raiseException(exception)
        if self._refreshTimer.isActive():
            self._refreshTimer.stop()
        if self._playlistManager.isRunning():
            self._playlistManager.abort()
        if len(self._segmentDownloaders) == 0:
            self._checkDone()
        else:
            App.FileDownloadManager.cancelDownloads(self._segmentDownloaders)