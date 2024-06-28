from Core import App
from Core.App import T
from Core.Config import Config
from Core.GlobalExceptions import Exceptions
from Download.Downloader.TwitchDownloader import TwitchDownloader
from Download.Downloader.Core.StreamDownloader import StreamDownloader
from Download.Downloader.Core.VideoDownloader import VideoDownloader
from Download.Downloader.Core.ClipDownloader import ClipDownloader
from Download.ScheduledDownloadManager import ScheduledDownload

from PyQt6 import QtCore

import uuid


class GlobalDownloadManager(QtCore.QObject):
    runningCountChangedSignal = QtCore.pyqtSignal(int)
    allCompletedSignal = QtCore.pyqtSignal()
    statsUpdated = QtCore.pyqtSignal(object, object)

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        App.DownloadManager.createdSignal.connect(self._downloadManagerDownloaderCreated)
        App.DownloadManager.startedSignal.connect(self._downloadManagerDownloadStarted)
        App.DownloadManager.completedSignal.connect(self._downloadManagerDownloadFinished)
        App.ScheduledDownloadManager.downloaderCreatedSignal.connect(self._scheduledDownloaderCreated)
        App.ScheduledDownloadManager.downloaderDestroyedSignal.connect(self._scheduledDownloaderDestroyed)
        App.ContentManager.restrictionsUpdated.connect(self.restrictionsUpdated)

    def setDownloaderCreationEnabled(self, enabled: bool) -> None:
        TwitchDownloader.setCreationEnabled(enabled)

    def _downloadManagerDownloaderCreated(self, downloaderId: uuid.UUID) -> None:
        App.DownloadHistory.createHistory(App.DownloadManager.get(downloaderId))

    def _scheduledDownloaderCreated(self, scheduledDownload: ScheduledDownload, downloader: StreamDownloader) -> None:
        App.DownloadHistory.createHistory(downloader)
        self.downloadStarted(downloader)
        if App.Preferences.general.isNotifyEnabled():
            App.Instance.notification.toastMessage(
                title=T("download-started"),
                message=f"{T('title')}: {downloader.downloadInfo.content.title}\n{T('file')}: {downloader.downloadInfo.getAbsoluteFileName()}",
                icon=App.Instance.notification.Icons.Information
            )

    def _scheduledDownloaderDestroyed(self, scheduledDownload: ScheduledDownload, downloader: StreamDownloader) -> None:
        self.downloadFinished(downloader)

    def _downloadManagerDownloadStarted(self, downloaderId: uuid.UUID) -> None:
        self.downloadStarted(App.DownloadManager.get(downloaderId))

    def _downloadManagerDownloadFinished(self, downloaderId: uuid.UUID) -> None:
        self.downloadFinished(App.DownloadManager.get(downloaderId))

    def downloadStarted(self, downloader: StreamDownloader | VideoDownloader | ClipDownloader) -> None:
        self.runningCountChangedSignal.emit(len(self.getRunningDownloaders()))

    def downloadFinished(self, downloader: StreamDownloader | VideoDownloader | ClipDownloader) -> None:
        self.runningCountChangedSignal.emit(len(self.getRunningDownloaders()))
        if len(self.getRunningDownloaders()) == 0:
            self.allCompletedSignal.emit()
        if App.Preferences.general.isNotifyEnabled():
            if downloader.status.terminateState.isTrue():
                if isinstance(downloader.status.getError(), Exceptions.AbortRequested):
                    title = "download-stopped" if downloader.downloadInfo.type.isStream() else "download-canceled"
                else:
                    title = "download-aborted"
            else:
                title = "download-complete"
            App.Instance.notification.toastMessage(
                title=T(title),
                message=f"{T('title')}: {downloader.downloadInfo.content.title}\n{T('file')}: {downloader.downloadInfo.getAbsoluteFileName()}",
                icon=App.Instance.notification.Icons.Information
            )
        self.updateDownloadStats(downloader)

    def updateDownloadStats(self, downloader: StreamDownloader | VideoDownloader | ClipDownloader) -> None:
        if downloader.status.terminateState.isTrue():
            if isinstance(downloader.status.getError(), Exceptions.AbortRequested):
                if not downloader.downloadInfo.type.isStream():
                    return
            else:
                return
        App.Preferences.temp.updateDownloadStats(downloader.progress.totalByteSize)
        downloadStats = App.Preferences.temp.getDownloadStats()
        totalFiles = downloadStats["totalFiles"]
        totalByteSize = downloadStats["totalByteSize"]
        if totalFiles < Config.SHOW_STATS[0]:
            showContributeInfo = totalFiles in Config.SHOW_STATS[1]
        else:
            showContributeInfo = totalFiles % Config.SHOW_STATS[0] == 0
        if showContributeInfo:
            self.statsUpdated.emit(totalFiles, totalByteSize)

    def restrictionsUpdated(self) -> None:
        downloaders = [downloader for downloader in self.getRunningDownloaders() if downloader.status.terminateState.isFalse()]
        contents = list({downloader.downloadInfo.content.id: downloader.downloadInfo.content for downloader in downloaders}.values())
        restrictions = App.ContentManager.checkRestrictions(contents)
        for restriction in restrictions:
            for downloader in downloaders:
                if downloader.downloadInfo.content.id == restriction.content.id:
                    if downloader.status.terminateState.isFalse():
                        downloader.abort(restriction)

    def cancelAll(self) -> None:
        App.DownloadManager.cancelAll()
        App.ScheduledDownloadManager.cancelAll()

    def getAllDownloaders(self) -> list[StreamDownloader | VideoDownloader | ClipDownloader]:
        return [*App.DownloadManager.downloaders, *App.ScheduledDownloadManager.getRunningDownloaders()]

    def getRunningDownloaders(self) -> list[StreamDownloader | VideoDownloader | ClipDownloader]:
        return [*App.DownloadManager.getRunningDownloaders(), *App.ScheduledDownloadManager.getRunningDownloaders()]

    def isDownloaderRunning(self) -> bool:
        return len(self.getRunningDownloaders()) != 0

    def isShuttingDown(self) -> bool:
        return not any(downloader.status.terminateState.isFalse() for downloader in self.getRunningDownloaders())