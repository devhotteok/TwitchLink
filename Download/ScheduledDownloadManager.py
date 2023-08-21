from Core import App
from Core.GlobalExceptions import Exceptions
from Services.Utils.Utils import Utils
from Services.Twitch.GQL import TwitchGQLAPI
from Services.Twitch.GQL import TwitchGQLModels
from Services.Twitch.Playback import TwitchPlaybackGenerator
from Services.Twitch.Playback import TwitchPlaybackModels
from Services.Twitch.PubSub.TwitchPubSub import PubSubEvent
from Services.Twitch.PubSub.TwitchPubSubEvents import EventTypes
from Services.FileNameLocker import FileNameLocker
from Download.DownloadInfo import DownloadInfo
from Download.Downloader.TwitchDownloader import TwitchDownloader
from Download.Downloader.Core.StreamDownloader import StreamDownloader
from Download.Downloader.Core.Engine.Config import Config
from Download.ScheduledDownloadPreset import ScheduledDownloadPreset
from Download.ScheduledDownloadPubSubManager import ScheduledDownloadPubSubSubscriber
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator

from PyQt6 import QtCore

import uuid


class ScheduledDownloadStatus(QtCore.QObject):
    updated = QtCore.pyqtSignal()

    NONE = 0
    GENERATING_PLAYBACK = 1
    DOWNLOADING = 2
    ERROR = 3
    DOWNLOADER_ERROR = 4

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.setNone()

    def setNone(self) -> None:
        self._status = self.NONE
        self._error = None
        self.updated.emit()

    def setGeneratingPlayback(self) -> None:
        self._status = self.GENERATING_PLAYBACK
        self._error = None
        self.updated.emit()

    def setDownloading(self) -> None:
        self._status = self.DOWNLOADING
        self._error = None
        self.updated.emit()

    def setError(self, error: Exception) -> None:
        self._status = self.ERROR
        self._error = error
        self.updated.emit()

    def setDownloaderError(self, error: Exception) -> None:
        self._status = self.DOWNLOADER_ERROR
        self._error = error
        self.updated.emit()

    def isNone(self) -> bool:
        return self._status == self.NONE

    def isGeneratingPlayback(self) -> bool:
        return self._status == self.GENERATING_PLAYBACK

    def isDownloading(self) -> bool:
        return self._status == self.DOWNLOADING

    def isError(self) -> bool:
        return self._status == self.ERROR

    def isDownloaderError(self) -> bool:
        return self._status == self.DOWNLOADER_ERROR

    def getError(self) -> Exception:
        return self._error

    def cleanup(self) -> None:
        if self.isError() or self.isDownloaderError():
            self.setNone()


class ScheduledDownload(QtCore.QObject):
    activeChanged = QtCore.pyqtSignal()
    channelDataUpdateStarted = QtCore.pyqtSignal()
    channelDataUpdateFinished = QtCore.pyqtSignal()
    channelDataUpdated = QtCore.pyqtSignal()
    pubSubStateChanged = QtCore.pyqtSignal()
    downloaderCreated = QtCore.pyqtSignal(object, object)
    downloaderDestroyed = QtCore.pyqtSignal(object, object)

    STREAM_PREVIEW_IMAGE_URL_FORMAT = "https://static-cdn.jtvnw.net/previews-ttv/live_user_{login}-{{width}}x{{height}}.jpg"
    GAME_BOX_ART_URL_FORMAT = "https://static-cdn.jtvnw.net/ttv-boxart/{id}-{{width}}x{{height}}.jpg"

    def __init__(self, scheduledDownloadPreset: ScheduledDownloadPreset, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._blocked = True
        self.uuid = uuid.uuid4()
        self.preset = scheduledDownloadPreset
        self.channel = None
        self._pubSubSubscriber: ScheduledDownloadPubSubSubscriber | None = None
        self._updatingChannelData = False
        self._autoUpdateTimer = QtCore.QTimer(parent=self)
        self._autoUpdateTimer.setInterval(Config.CHANNEL_AUTO_UPDATE_INTERVAL)
        self._autoUpdateTimer.timeout.connect(self.updateChannelData)
        self.downloader: StreamDownloader | None = None
        self.status = ScheduledDownloadStatus(parent=self)
        self.updateChannelData()

    def getId(self) -> uuid.UUID:
        return self.uuid

    def setBlocked(self, blocked: bool) -> None:
        if blocked != self.isBlocked():
            self._blocked = blocked
            self._syncEnabledState()
            if not self._blocked:
                self.updateChannelData()
            self.activeChanged.emit()

    def isBlocked(self) -> bool:
        return self._blocked

    def setEnabled(self, enabled: bool) -> None:
        if enabled != self.preset.isEnabled():
            self.preset.setEnabled(enabled)
            self.status.cleanup()
            self._syncEnabledState()
            self.activeChanged.emit()

    def isEnabled(self) -> bool:
        return self.preset.isEnabled()

    def isActive(self) -> bool:
        return not self.isBlocked() and self.isEnabled()

    def _syncEnabledState(self) -> None:
        if self.isChannelRetrieved():
            if self.isActive():
                self.connectPubSub()
                self.startDownloadIfOnline()
            else:
                self.disconnectPubSub()
                if self.status.isDownloading():
                    self.downloader.cancel()
                elif self.status.isError() or self.status.isDownloaderError():
                    self.status.setNone()
            self._syncAutoUpdate()

    def isChannelRetrieved(self) -> bool:
        return self.channel != None

    def isPubSubConnected(self) -> bool:
        return self._pubSubSubscriber != None

    def isSubscribed(self) -> bool:
        return self.isPubSubConnected() and self._pubSubSubscriber.isSubscribed()

    def isConnecting(self) -> bool:
        return self.isPubSubConnected() and self._pubSubSubscriber.hasPendingRequest()

    def connectPubSub(self) -> None:
        if not self.isPubSubConnected():
            self._pubSubSubscriber = App.ScheduledDownloadPubSubManager.subscribe(self.channel.id, key=self.getId())
            self._pubSubSubscriber.stateChanged.connect(self.pubSubStateChanged)
            self._pubSubSubscriber.eventReceived.connect(self.pubSubEventHandler)
            self.pubSubStateChanged.emit()

    def disconnectPubSub(self) -> None:
        if self.isPubSubConnected():
            App.ScheduledDownloadPubSubManager.unsubscribe(self.channel.id, key=self.getId())
            self._pubSubSubscriber = None
            self.pubSubStateChanged.emit()

    def _syncAutoUpdate(self) -> None:
        if self.isActive() and self.isChannelRetrieved() and self.isOffline():
            self._autoUpdateTimer.start()
        else:
            self._autoUpdateTimer.stop()

    def canStartDownload(self) -> bool:
        return self.isActive() and self.isChannelRetrieved() and self.isOnline() and not self.status.isGeneratingPlayback() and not self.status.isDownloading()

    def isUpdatingChannelData(self) -> bool:
        return self._updatingChannelData

    def updateChannelData(self) -> None:
        if not self.isUpdatingChannelData():
            self._updatingChannelData = True
            self.channelDataUpdateStarted.emit()
            if self.isChannelRetrieved():
                App.TwitchGQL.getChannel(id=self.channel.id).finished.connect(self._channelDataUpdateResult)
            else:
                App.TwitchGQL.getChannel(login=self.preset.channel).finished.connect(self._channelDataUpdateResult)

    def _channelDataUpdateResult(self, response: TwitchGQLAPI.TwitchGQLResponse) -> None:
        if response.getError() == None:
            isFirst = not self.isChannelRetrieved()
            self.channel = response.getData()
            self.channelDataUpdated.emit()
            if isFirst:
                self._syncEnabledState()
            else:
                self.startDownloadIfOnline()
        self._updatingChannelData = False
        self.channelDataUpdateFinished.emit()

    def setOnline(self) -> None:
        if self.isOffline():
            self.channel.stream = TwitchGQLModels.Stream({
                "title": self.channel.lastBroadcast.title,
                "previewImageURL": "" if self.channel.login == "" else self.STREAM_PREVIEW_IMAGE_URL_FORMAT.format(login=self.channel.login),
                "broadcaster": {
                    "id": self.channel.id,
                    "login": self.channel.login,
                    "displayName": self.channel.displayName
                }
            })
            self.channel.stream.game = self.channel.lastBroadcast.game
            self.channel.stream.createdAt = QtCore.QDateTime.currentDateTimeUtc()
            self.channelDataUpdated.emit()
            self._syncAutoUpdate()

    def setOffline(self) -> None:
        if self.isOnline():
            self.channel.stream = None
            self.channelDataUpdated.emit()
            self._syncAutoUpdate()

    def isOnline(self) -> bool:
        return self.channel.stream != None

    def isOffline(self) -> bool:
        return not self.isOnline()

    def pubSubEventHandler(self, event: PubSubEvent) -> None:
        topic, data = event.topic, event.data
        if topic.eventType == EventTypes.VideoPlaybackById:
            if data["type"] == "stream-up":
                self.setOnline()
                self.channel.stream.createdAt = QtCore.QDateTime.fromSecsSinceEpoch(data["server_time"], QtCore.Qt.TimeSpec.UTC)
            elif data["type"] == "stream-down":
                self.setOffline()
                self.channel.lastBroadcast.startedAt = QtCore.QDateTime.fromSecsSinceEpoch(data["server_time"], QtCore.Qt.TimeSpec.UTC)
            elif data["type"] == "viewcount":
                if self.isOnline() and self.channel.stream.id != None:
                    self.channel.stream.viewersCount = data["viewers"]
                else:
                    self.updateChannelData()
            elif data["type"] == "commercial":
                pass
        elif topic.eventType == EventTypes.BroadcastSettingsUpdate:
            self.channel.lastBroadcast.title = data["status"]
            if data["game_id"] == 0:
                gameData = {}
            else:
                gameData = {
                    "id": data["game_id"],
                    "name": data["game"],
                    "boxArtURL": self.GAME_BOX_ART_URL_FORMAT.format(id=data["game_id"]),
                    "displayName": data["game"]
                }
            self.channel.lastBroadcast.game = TwitchGQLModels.Game(gameData)
            if self.isOnline():
                self.channel.stream.title = self.channel.lastBroadcast.title
                self.channel.stream.game = self.channel.lastBroadcast.game
        self.channelDataUpdated.emit()
        self.startDownloadIfOnline()

    def startDownloadIfOnline(self) -> None:
        if self.canStartDownload():
            self.generateStreamPlayback()

    def generateStreamPlayback(self) -> None:
        try:
            App.ContentManager.checkRestriction(self.channel.stream)
        except Exception as e:
            self.status.setError(e)
        else:
            self.status.setGeneratingPlayback()
            TwitchPlaybackGenerator.TwitchStreamPlaybackGenerator(self.channel.stream.broadcaster.login, parent=self).finished.connect(self._processStreamPlaybackResult)

    def _processStreamPlaybackResult(self, generator: TwitchPlaybackGenerator.TwitchStreamPlaybackGenerator) -> None:
        if generator.getError() == None:
            if self.isActive() and self.isOnline():
                streamPlayback = generator.getData()
                try:
                    self.createDownloader(streamPlayback)
                except Exception as e:
                    self.status.setError(e)
            else:
                self.status.setNone()
        elif isinstance(generator.getError(), TwitchPlaybackGenerator.Exceptions.ChannelIsOffline):
            self.setOffline()
            self.status.setNone()
        else:
            if self.isActive():
                self.status.setError(generator.getError())
            else:
                self.status.setNone()

    def createDownloader(self, playback: TwitchPlaybackModels.TwitchStreamPlayback) -> None:
        downloadInfo = DownloadInfo(self.channel.stream, playback)
        downloadInfo.setDirectory(self.preset.directory)
        selectedResolution = self.preset.selectResolution(playback.getResolutions())
        downloadInfo.setResolution(playback.getResolutions().index(selectedResolution))
        downloadInfo.setAbsoluteFileName(Utils.createUniqueFile(downloadInfo.directory, FileNameGenerator.generateFileName(self.channel.stream, selectedResolution, filenameTemplate=self.preset.filenameTemplate), self.preset.fileFormat, exclude=FileNameLocker.getLockedFiles()))
        downloadInfo.setRemuxEnabled(self.preset.isRemuxEnabled())
        self.downloader = TwitchDownloader.create(downloadInfo, parent=self)
        self.downloader.finished.connect(self.downloadResultHandler)
        self.downloaderCreated.emit(self, self.downloader)
        self.status.setDownloading()
        self.downloader.start()

    def downloadResultHandler(self, downloader: StreamDownloader) -> None:
        error = downloader.status.getError()
        if error == None:
            self.setOffline()
            self.status.setNone()
        elif self.isActive():
            self.status.setDownloaderError(error)
        else:
            self.status.setNone()
        downloader.deleteLater()
        self.downloader = None
        self.downloaderDestroyed.emit(self, downloader)
        if isinstance(error, Exceptions.NetworkError):
            self.startDownloadIfOnline()

    def isDownloading(self) -> bool:
        return self.downloader != None

    def __del__(self):
        if self.isPubSubConnected():
            try:
                App.ScheduledDownloadPubSubManager.unsubscribe(self.channel.id, key=self.getId())
            except:
                pass


class ScheduledDownloadManager(QtCore.QObject):
    blockedChangedSignal = QtCore.pyqtSignal(bool)
    enabledChangedSignal = QtCore.pyqtSignal(bool)
    createdSignal = QtCore.pyqtSignal(object)
    destroyedSignal = QtCore.pyqtSignal(object)
    downloaderCreatedSignal = QtCore.pyqtSignal(object, object)
    downloaderDestroyedSignal = QtCore.pyqtSignal(object, object)
    downloaderCountChangedSignal = QtCore.pyqtSignal(int)

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._blocked = True
        self._enabled = False
        self.scheduledDownloads: dict[uuid.UUID, ScheduledDownload] = {}
        self.runningScheduledDownloads: list[ScheduledDownload] = []
        self._syncState()

    def setBlocked(self, blocked: bool) -> None:
        if blocked != self._blocked:
            self._blocked = blocked
            self._syncState()
            self.blockedChangedSignal.emit(self._blocked)

    def isBlocked(self) -> bool:
        return self._blocked

    def setEnabled(self, enabled: bool) -> None:
        if enabled != self._enabled:
            self._enabled = enabled
            self._syncState()
            self.enabledChangedSignal.emit(self._enabled)

    def isEnabled(self) -> bool:
        return self._enabled

    def _syncState(self) -> None:
        self._syncScheduledDownloadsBlockedState()
        self._updatePubSubState()

    def _syncScheduledDownloadsBlockedState(self) -> None:
        blocked = not self.isEnabled() or self.isBlocked()
        for scheduledDownload in self.scheduledDownloads.values():
            scheduledDownload.setBlocked(blocked)

    def _updatePubSubState(self) -> None:
        if not self.isBlocked() and self.isEnabled() and any(scheduledDownload.isEnabled() for scheduledDownload in self.scheduledDownloads.values()):
            if not App.ScheduledDownloadPubSubManager.isOpened():
                App.ScheduledDownloadPubSubManager.open()
        else:
            if App.ScheduledDownloadPubSubManager.isOpened():
                App.ScheduledDownloadPubSubManager.close()

    def setPresets(self, presetList: list[ScheduledDownloadPreset]) -> None:
        for scheduledDownload in self.getScheduledDownloads():
            self.remove(scheduledDownload.getId())
        for scheduledDownloadPreset in presetList:
            self.create(scheduledDownloadPreset)

    def getPresets(self) -> list[ScheduledDownloadPreset]:
        return [scheduledDownload.preset for scheduledDownload in self.getScheduledDownloads()]

    def create(self, scheduledDownloadPreset: ScheduledDownloadPreset) -> uuid.UUID:
        scheduledDownload = ScheduledDownload(scheduledDownloadPreset, parent=self)
        scheduledDownload.activeChanged.connect(self._updatePubSubState)
        scheduledDownload.downloaderCreated.connect(self.downloaderCreated)
        scheduledDownload.downloaderDestroyed.connect(self.downloaderDestroyed)
        scheduledDownloadId = scheduledDownload.getId()
        self.scheduledDownloads[scheduledDownloadId] = scheduledDownload
        self.createdSignal.emit(scheduledDownloadId)
        self._syncState()
        return scheduledDownloadId

    def downloaderCreated(self, scheduledDownload: ScheduledDownload, downloader: StreamDownloader) -> None:
        self.runningScheduledDownloads.append(scheduledDownload)
        self.downloaderCountChangedSignal.emit(len(self.getRunningDownloaders()))
        self.downloaderCreatedSignal.emit(scheduledDownload, downloader)

    def downloaderDestroyed(self, scheduledDownload: ScheduledDownload, downloader: StreamDownloader) -> None:
        self.runningScheduledDownloads.remove(scheduledDownload)
        self.downloaderCountChangedSignal.emit(len(self.getRunningDownloaders()))
        self.downloaderDestroyedSignal.emit(scheduledDownload, downloader)

    def get(self, scheduledDownloadId: uuid.UUID) -> ScheduledDownload:
        return self.scheduledDownloads[scheduledDownloadId]

    def remove(self, scheduledDownloadId: uuid.UUID) -> None:
        if not self.scheduledDownloads[scheduledDownloadId].isDownloading():
            self.scheduledDownloads.pop(scheduledDownloadId).deleteLater()
            self.destroyedSignal.emit(scheduledDownloadId)
            self._syncState()

    def cancelAll(self) -> None:
        for downloader in self.getRunningDownloaders():
            downloader.cancel()

    def getScheduledDownloadKeys(self) -> list[uuid.UUID]:
        return list(self.scheduledDownloads.keys())

    def getScheduledDownloads(self) -> list[ScheduledDownload]:
        return list(self.scheduledDownloads.values())

    def getRunningScheduledDownloads(self) -> list[ScheduledDownload]:
        return self.runningScheduledDownloads

    def getRunningDownloaders(self) -> list[StreamDownloader]:
        return [scheduledDownloads.downloader for scheduledDownloads in self.getRunningScheduledDownloads()]

    def isDownloaderRunning(self) -> bool:
        return len(self.getRunningDownloaders()) != 0