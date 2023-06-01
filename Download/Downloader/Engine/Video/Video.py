from Download.Downloader.Engine.Video.Playlist.OnlinePlaylistManager import OnlinePlaylistManager
from .SegmentDownloader import SegmentDownloader

from Download.Downloader.Engine.Setup import EngineSetup
from Download.Downloader.Engine.ThreadPool import DownloadThreadPool
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
        self.taskManager = TaskManager(DownloadThreadPool, parent=self)

    def download(self):
        try:
            self.setupSegmentDownload()
            self.downloadSegments()
            self.encode()
            self.removeTempFiles()
        except Exception as e:
            self.removeTempFiles()
            raise e

    def setupSegmentDownload(self):
        try:
            self.tempDirectory = TempManager.createTempDirectory(self.setup.downloadInfo.directory)
            self.logger.info(f"Temp Directory: {self.tempDirectory.name}")
        except Exception as e:
            self.logger.exception(e)
            raise Exceptions.FileSystemError
        self.playlistManager = OnlinePlaylistManager(
            url=self.setup.downloadInfo.getUrl(),
            filePath=Utils.joinPath(self.tempDirectory.name, f"{Config.PLAYLIST_FILE_NAME}.m3u8"),
            strictMode=self.setup.downloadInfo.isClippingModeEnabled()
        )
        self.playlistManager.setRange(*self.setup.downloadInfo.range)
        self.syncPlaylistProgress()

    def syncPlaylistProgress(self):
        self.progress.totalFiles = len(self.playlistManager.getSegments())
        self.progress.totalMilliseconds = self.playlistManager.totalMilliseconds
        self.logger.info(f"Total Segments: {self.progress.totalFiles}")
        self.logger.info(f"Total Seconds: {self.progress.totalSeconds}")
        self.syncData({"playlistManager": self.playlistManager})

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
            for segment in self.playlistManager.getSegments():
                if segment.fileName not in processedFiles:
                    processedFiles.append(segment.fileName)
                    self.taskManager.add(
                        SegmentDownloader(
                            url=url,
                            segment=segment,
                            unmute=self.setup.unmuteVideo,
                            saveAs=Utils.joinPath(self.tempDirectory.name, segment.fileName),
                            priority=self.setup.priority + 1 if self.status.isUpdateFound() else self.setup.priority
                        )
                    )
            self.taskManager.waitForDone()
            if not (self.setup.updateTrack and self.setup.downloadInfo.range[1] == None):
                break
            if self.status.terminateState.isProcessing() or self.status.isDownloadSkipped():
                break
            if not self.getUpdates():
                break

    def getUpdates(self):
        self.status.setWaitingCount(0)
        while self.status.getWaitingCount() < Config.UPDATE_TRACK_MAX_RETRY_COUNT:
            self.status.setWaiting()
            self.status.setWaitingCount(self.status.getWaitingCount() + 1)
            self.logger.info(f"Waiting for Updates... {self.status.getWaitingCount()}/{Config.UPDATE_TRACK_MAX_RETRY_COUNT}")
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
                    self.status.setWaitingCount(Config.UPDATE_TRACK_MAX_RETRY_COUNT)
                    break
                self.msleep(200)
            self.status.setWaitingTime(None)
            self.status.setUpdating()
            self.syncStatus()
            if self.status.terminateState.isProcessing() or self.status.isDownloadSkipped():
                break
            prevFiles = self.playlistManager.getFileList()
            try:
                self.logger.info("Updating Playlist...")
                self.playlistManager.updatePlaylist()
                self.syncPlaylistProgress()
                if self.status.terminateState.isProcessing() or self.status.isDownloadSkipped():
                    break
                if prevFiles == self.playlistManager.getFileList():
                    self.logger.info("Update Not Found")
                else:
                    self.logger.info("Update Found")
                    self.status.setUpdateFound()
                    return True
            except:
                pass
        return False

    def segmentDownloadComplete(self, task):
        if task.result.success:
            if self.setup.unmuteVideo and task.result.data.muted:
                self.logger.warning(f"Failed to unmute segment: {task.segment.fileName}")
                self.progress.mutedFiles += 1
                self.progress.mutedMilliseconds += task.segment.durationMilliseconds
        else:
            urls = "\n".join(segmentUrl.url for segmentUrl in task.segmentUrls)
            self.logger.warning(f"Failed to download segment: {task.segment.fileName} [{task.result.error}]\n{urls}")
            if isinstance(task.result.error, Exceptions.FileSystemError):
                self.abort(task.result.error)
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
            trimFrom, trimTo = self.playlistManager.getTrimRange()
            self.FFmpeg.startEncodingProcess(
                target=self.playlistManager.filePath,
                saveAs=self.setup.downloadInfo.getAbsoluteFileName(),
                trimFrom=None if trimFrom == None else trimFrom / 1000,
                trimTo=None if trimTo == None else trimTo / 1000,
                remux=not self.setup.downloadInfo.isClippingModeEnabled()
            )
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
                self.progress.missingMilliseconds += self.playlistManager.getSegments()[missing].durationMilliseconds
            time = progress.get("time")
            if time != None:
                self.progress.milliseconds = max(0, Utils.toSeconds(*time.split(".")[0].split(":")) * 1000 + int(time.split(".")[1][:3]))
            size = progress.get("size") or progress.get("Lsize")
            if size != None:
                self.progress.totalByteSize = max(0, Utils.getByteSize(size))
                self.progress.byteSize = self.progress.totalByteSize
            self.syncProgress()

    def removeFile(self, fileName):
        try:
            Utils.removeFile(fileName)
        except:
            pass

    def removeTempFiles(self):
        self.logger.info("Cleaning up...")
        try:
            if hasattr(self, "playlistManager"):
                self.playlistManager.closeFile()
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