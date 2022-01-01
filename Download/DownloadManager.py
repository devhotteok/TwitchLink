from Core.App import App
from Core.GlobalExceptions import Exceptions
from Services.Messages import Messages
from Services.Utils.Utils import Utils
from Services.Translator.Translator import T
from Database.Database import DB
from Download.Downloader.Engine.Engine import TwitchDownloader


class _DownloadManager:
    def __init__(self):
        self.downloaders = {}

    def start(self, *args, **kwargs):
        downloader = TwitchDownloader(*args, **kwargs)
        downloader.hasUpdate.connect(self.handleDownloader)
        downloader.done.connect(self.handleDownloadResult)
        downloaderId = id(downloader)
        self.downloaders[downloaderId] = downloader
        downloader.start()
        return downloaderId

    def get(self, downloaderId):
        return self.downloaders[downloaderId]

    def cancelAll(self):
        for downloader in self.downloaders.values():
            downloader.cancel()

    def waitAll(self):
        for downloader in self.downloaders.values():
            downloader.wait()

    def remove(self, downloaderId):
        self.downloaders[downloaderId].cancel()
        self.downloaders[downloaderId].wait()
        del self.downloaders[downloaderId]

    def removeAll(self):
        self.cancelAll()
        self.waitAll()
        self.downloaders = {}

    def isDownloaderRunning(self):
        for downloader in self.downloaders.values():
            if downloader.isRunning():
                return True
        return False

    def isShuttingDown(self):
        for downloader in self.downloaders.values():
            if downloader.status.terminateState.isFalse():
                return False
        return True

    def getRunningDownloadersCount(self):
        return sum(1 for downloader in self.downloaders.values() if downloader.isRunning())

    def handleDownloader(self, downloader):
        downloadersCount = self.getRunningDownloadersCount()
        if downloadersCount == 0:
            App.taskbar.complete()
        if downloadersCount == 1:
            downloadType = downloader.setup.downloadInfo.type
            status = downloader.status
            progress = downloader.progress
            if downloadType.isVideo():
                if status.isEncoding():
                    App.taskbar.setValue(progress.timeProgress)
                else:
                    App.taskbar.setValue(progress.fileProgress)
            elif downloadType.isClip():
                App.taskbar.setValue(progress.byteSizeProgress)
            if not status.terminateState.isFalse():
                App.taskbar.stop()
            elif not status.pauseState.isFalse() or status.isWaiting() or status.isEncoding():
                App.taskbar.pause()
            elif not App.taskbar.isVisible():
                App.taskbar.show(indeterminate=downloadType.isStream())
        else:
            App.taskbar.hide()

    def handleDownloadResult(self, downloader):
        if downloader.status.terminateState.isTrue():
            error = downloader.status.getError()
            if error != None:
                if error == Exceptions.FileSystemError:
                    Utils.info(*Messages.INFO.FILE_SYSTEM_ERROR)
                elif error == Exceptions.NetworkError:
                    Utils.info(*Messages.INFO.NETWORK_ERROR)
                else:
                    Utils.info(*Messages.INFO.DOWNLOAD_ERROR)
        elif DB.general.isAutoCloseEnabled() and not downloader.setup.downloadInfo.type.isClip():
            App.exit()
        else:
            fileName = downloader.setup.downloadInfo.getAbsoluteFileName()
            if Utils.ask(
                "download-complete",
                "{}\n\n{}".format(T("#Download completed."), fileName),
                okText="open",
                cancelText="ok"
            ):
                try:
                    Utils.openFile(fileName)
                except:
                    Utils.info(*Messages.INFO.FILE_NOT_FOUND)


DownloadManager = _DownloadManager()