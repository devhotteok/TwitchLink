from .PlaylistManager import Playlist
from .SegmentDownloader import SegmentDownloader

from Download.Downloader.Engine.Setup import EngineSetup
from Download.Downloader.Engine.ThreadPool import ThreadPool
from Download.Downloader.Engine.Config import Config

from Core.GlobalExceptions import Exceptions
from Services.Utils.Utils import Utils
from Services.Temp.TempManager import TempManager
from Services.Task.TaskManager import TaskManager
from Download.Downloader.FFmpeg.FFmpeg import FFmpeg

import math
import time


class VideoDownloader(EngineSetup):
    def __init__(self, downloadInfo, parent=None):
        super(VideoDownloader, self).__init__(downloadInfo, parent=parent)
        self.FFmpeg = FFmpeg(parent=self)
        self.taskManager = TaskManager(ThreadPool, parent=self)

    def download(self):
        self.setupSegmentDownload()
        self.downloadSegments()
        self.encode()
        self.removeTempFiles()

    def setupSegmentDownload(self):
        try:
            self.tempDirectory = TempManager.createTempDirectory(self.setup.downloadInfo.directory)
            self.logger.info(f"Temp Directory: {self.tempDirectory.name}")
        except Exception as e:
            self.logger.exception(e)
            raise Exceptions.FileSystemError
        self.playlist = Playlist(
            self.setup.downloadInfo.getUrl(),
            Utils.joinPath(self.tempDirectory.name, f"{Config.PLAYLIST_FILE_NAME}.m3u8")
        )
        self.playlist.setRange(*self.setup.downloadInfo.range)
        self.syncPlaylistProgress()

    def syncPlaylistProgress(self):
        self.logger.info(f"Total Segments: {len(self.playlist.getSegments())}")
        self.logger.info(f"Total Seconds: {int(self.playlist.totalSeconds)}")
        self.progress.totalFiles = len(self.playlist.segments)
        self.progress.totalSeconds = self.playlist.totalSeconds
        self.syncData({"playlist": self.playlist})

    def downloadSegments(self):
        url = self.setup.downloadInfo.getUrl().rsplit("/", 1)[0]
        processedFiles = []
        with self.actionLock:
            self.taskManager.taskCompleteSignal.connect(self.segmentDownloadComplete)
            self.taskManager.ifPaused.connect(self.taskPaused)
            self.taskManager.start()
        while self.status.terminateState.isFalse():
            self.status.setDownloading()
            self.syncStatus()
            self.logger.info("Downloading Segments...")
            for segment in self.playlist.getSegments():
                if segment.fileName not in processedFiles:
                    processedFiles.append(segment.fileName)
                    segmentDownloader = SegmentDownloader(
                        url=url,
                        segment=segment,
                        unmute=self.setup.unmuteVideo,
                        saveAs=Utils.joinPath(self.tempDirectory.name, segment.fileName),
                        priority=self.setup.priority + 1 if self.status.isUpdateFound() else self.setup.priority
                    )
                    self.taskManager.add(task=segmentDownloader)
            self.taskManager.waitForDone()
            if not (self.setup.updateTrack and self.playlist.timeRange.timeTo == None):
                break
            if self.status.terminateState.isProcessing() or self.status.isDownloadSkipped():
                break
            self.logger.info("Waiting for Updates...")
            self.status.setWaiting()
            waitEnd = time.time() + Config.UPDATE_TRACK_DURATION
            while True:
                prevWaiting = self.status.getWaitingTime()
                self.status.setWaitingTime(math.ceil(waitEnd - time.time()))
                if self.status.getWaitingTime() != prevWaiting:
                    self.syncStatus()
                if self.status.getWaitingTime() <= 0 or self.status.terminateState.isProcessing() or self.status.isDownloadSkipped():
                    break
                if self.status.isWaitingSkipped():
                    self.status.setSkipWaiting(False)
                    break
                self.msleep(200)
            self.status.setWaitingTime(None)
            self.status.setUpdating()
            self.syncStatus()
            if self.status.terminateState.isProcessing() or self.status.isDownloadSkipped():
                break
            prevFiles = self.playlist.getFileList()
            try:
                self.logger.info("Updating Playlist...")
                self.playlist.updatePlaylist()
                self.syncPlaylistProgress()
                if prevFiles == self.playlist.getFileList():
                    self.logger.info("Update Not Found")
                    break
                else:
                    self.logger.info("Update Found")
                    self.status.setUpdateFound()
            except:
                break

    def segmentDownloadComplete(self, task):
        if not task.result.success:
            urls = "\n".join(task.urls)
            self.logger.warning(f"Failed to download segment: {task.segment.fileName} [{task.result.error}]\n{urls}")
            if isinstance(task.result.error, Exceptions.FileSystemError):
                self.cancel()
                self.status.raiseError(Exceptions.FileSystemError)
                return
        self.progress.file += 1
        self.syncProgress()

    def encode(self):
        with self.actionLock:
            if self.status.terminateState.isProcessing():
                return
            self.status.setEncoding()
            self.syncStatus()
            self.logger.info("Encoding...")
            self.FFmpeg.start(self.playlist.filePath, self.setup.downloadInfo.getAbsoluteFileName())
        processingFile = None
        for progress in self.FFmpeg.output(logger=self.logger):
            file = progress.get("file")
            if file != None:
                if processingFile != None:
                    self.removeFile(processingFile)
                processingFile = file
            missing = progress.get("missing")
            if missing != None:
                self.progress.missingFiles += 1
                self.progress.missingSeconds += self.playlist.getSegments()[missing].duration
            time = progress.get("time")
            if time != None:
                self.progress.seconds = Utils.toSeconds(*time.split(".")[0].split(":"))
            size = progress.get("size") or progress.get("Lsize")
            if size != None:
                self.progress.totalSize = Utils.formatByteSize(size)
                self.progress.size = self.progress.totalSize
            self.syncProgress()

    def removeFile(self, fileName):
        try:
            Utils.removeFile(fileName)
        except:
            pass

    def removeTempFiles(self):
        self.logger.info("Cleaning up...")
        try:
            self.playlist.closeFile()
        except Exception as e:
            self.logger.exception(e)
        try:
            self.tempDirectory.cleanup()
        except Exception as e:
            self.logger.exception(e)

    def cancel(self):
        with self.actionLock:
            if self.isRunning() and not self.status.isDone() and self.status.terminateState.isFalse():
                self.logger.warning("[ACTION] Cancel")
                self.status.terminateState.setProcessing()
                self.syncStatus()
                self.taskManager.stop()
                if self.FFmpeg.process != None:
                    self.FFmpeg.kill()

    def pause(self):
        if self.status.pauseState.isFalse():
            self.logger.warning("[ACTION] Pause")
            self.status.pauseState.setProcessing()
            self.syncStatus()
            self.taskManager.pause()

    def resume(self):
        if self.status.pauseState.isTrue():
            self.logger.warning("[ACTION] Resume")
            self.taskManager.resume()
            self.status.pauseState.setFalse()
            self.syncStatus()

    def taskPaused(self):
        self.logger.warning("[ACTION:RESULT] Paused")
        self.status.pauseState.setTrue()
        self.syncStatus()

    def skipWaiting(self):
        self.logger.warning("[ACTION] Skip Waiting")
        self.status.setSkipWaiting(True)
        self.syncStatus()

    def skipDownload(self):
        if not self.status.isDownloadSkipped():
            self.logger.warning("[ACTION] Skip Download")
            self.status.setDownloadSkip()
            self.syncStatus()
            with self.actionLock:
                self.taskManager.stop()