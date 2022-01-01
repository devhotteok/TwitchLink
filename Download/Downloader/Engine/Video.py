from .Setup import EngineSetup
from .Config import Config

from Core.GlobalExceptions import Exceptions
from Services.Utils.Utils import Utils
from Services.Temp.TempManager import TempManager
from Download.Downloader.PlaylistManager import Playlist
from Download.Downloader.SegmentDownloader import SegmentDownloader
from Download.Downloader.Task.TaskManager import TaskManager
from Download.Downloader.Task.ThreadPool import ThreadPool
from Download.Downloader.FFmpeg.FFmpeg import FFmpeg

import math
import time


class VideoDownloader(EngineSetup):
    def __init__(self, downloadInfo, **kwargs):
        super().__init__(downloadInfo, **kwargs)
        self.FFmpeg = None
        self.taskManager = TaskManager(ThreadPool)

    def run(self):
        try:
            self.setupSegmentDownload()
            self.downloadSegments()
            self.encode()
            self.removeTempFiles()
        except Exception as e:
            self.status.raiseError(type(e))
        with self.actionLock:
            if self.status.terminateState.isProcessing():
                self.status.terminateState.setTrue()
            self.status.setDone()
            self.syncStatus()

    def setupSegmentDownload(self):
        try:
            self.tempDirectory = TempManager.createTempDirectory(self.setup.downloadInfo.directory)
        except:
            raise Exceptions.FileSystemError
        self.playlist = Playlist(
            self.setup.downloadInfo.getUrl(),
            Utils.joinPath(self.tempDirectory.name, "{}.m3u8".format(Config.PLAYLIST_FILE_NAME))
        )
        self.playlist.setRange(*self.setup.downloadInfo.range)
        self.syncPlaylistProgress()

    def syncPlaylistProgress(self):
        self.progress.totalFiles = len(self.playlist.segments)
        self.progress.totalSeconds = self.playlist.totalSeconds
        self.syncData({"playlist": self.playlist})

    def downloadSegments(self):
        url = self.setup.downloadInfo.getUrl().rsplit("/", 1)[0]
        processedFiles = []
        with self.actionLock:
            self.taskManager.taskCompleteSignal.connect(self.segmentDownloadResult)
            self.taskManager.ifPaused.connect(self.taskPaused)
            self.taskManager.start()
        while self.status.terminateState.isFalse():
            self.status.setDownloading()
            self.syncStatus()
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
                time.sleep(0.1)
            self.status.setWaitingTime(None)
            self.status.setUpdating()
            self.syncStatus()
            if self.status.terminateState.isProcessing() or self.status.isDownloadSkipped():
                break
            prevFiles = self.playlist.getFileList()
            try:
                self.playlist.updatePlaylist()
                self.syncPlaylistProgress()
                if prevFiles == self.playlist.getFileList():
                    break
                else:
                    self.status.setUpdateFound()
            except:
                break

    def segmentDownloadResult(self, result):
        if result.error == Exceptions.FileSystemError:
            self.status.raiseError(Exceptions.FileSystemError)
            self.killDownloadTasks()
        else:
            self.progress.file += 1
            self.syncProgress()

    def encode(self):
        with self.actionLock:
            if self.status.terminateState.isProcessing():
                return
            self.status.setEncoding()
            self.syncStatus()
            self.FFmpeg = FFmpeg(self.playlist.filePath, self.setup.downloadInfo.getAbsoluteFileName())
        processingFile = None
        for progress in self.FFmpeg.output():
            file = progress.get("file")
            if file != None:
                if processingFile != None:
                    self.removeFile(processingFile)
                processingFile = file
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
        try:
            self.playlist.closeFile()
        except:
            pass
        try:
            self.tempDirectory.cleanup()
        except:
            pass

    def cancel(self):
        with self.actionLock:
            if self.isRunning() and not self.status.isDone() and self.status.terminateState.isFalse():
                self.status.terminateState.setProcessing()
                self.syncStatus()
                self.taskManager.stop()
                if self.FFmpeg != None:
                    self.FFmpeg.kill()

    def pause(self):
        if self.status.pauseState.isFalse():
            self.status.pauseState.setProcessing()
            self.syncStatus()
            self.taskManager.pause()

    def resume(self):
        if self.status.pauseState.isTrue():
            self.taskManager.resume()
            self.status.pauseState.setFalse()
            self.syncStatus()

    def taskPaused(self):
        self.status.pauseState.setTrue()
        self.syncStatus()

    def skipWaiting(self):
        self.status.setSkipWaiting(True)

    def skipDownload(self):
        if not self.status.isDownloadSkipped():
            self.status.setDownloadSkip()
            self.syncStatus()
            with self.actionLock:
                self.taskManager.stop()