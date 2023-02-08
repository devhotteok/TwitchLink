from Core.Updater import Updater
from Services.Utils.Utils import Utils
from Services.Twitch.Gql import TwitchGqlModels
from Services.Twitch.Playback import TwitchPlaybackAccessTokens
from Services.Twitch.PubSub import TwitchPubSubEvents
from Services.AccessTokenGenerator import AccessTokenGenerator
from Services.FileNameManager import FileNameManager
from Search import Engine
from Download.DownloadInfo import DownloadInfo
from Download.Downloader.Engine.Engine import TwitchDownloader
from Download.ScheduledDownloadPubSub import ScheduledDownloadPubSub
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator

from PyQt5 import QtCore

import uuid


class ScheduledDownloadStatus(QtCore.QObject):
    updated = QtCore.pyqtSignal()

    NONE = 0
    GENERATING_ACCESS_TOKEN = 1
    DOWNLOADING = 2
    ERROR = 3
    DOWNLOADER_ERROR = 4

    def __init__(self, parent=None):
        super(ScheduledDownloadStatus, self).__init__(parent=parent)
        self.setNone()

    def setNone(self):
        self._status = self.NONE
        self._error = None
        self.updated.emit()

    def setGeneratingAccessToken(self):
        self._status = self.GENERATING_ACCESS_TOKEN
        self._error = None
        self.updated.emit()

    def setDownloading(self):
        self._status = self.DOWNLOADING
        self._error = None
        self.updated.emit()

    def setError(self, error):
        self._status = self.ERROR
        self._error = error
        self.updated.emit()

    def setDownloaderError(self, error):
        self._status = self.DOWNLOADER_ERROR
        self._error = error
        self.updated.emit()

    def getStatus(self):
        return self._status

    def isNone(self):
        return self._status == self.NONE

    def isGeneratingAccessToken(self):
        return self._status == self.GENERATING_ACCESS_TOKEN

    def isDownloading(self):
        return self._status == self.DOWNLOADING

    def isError(self):
        return self._status == self.ERROR

    def isDownloaderError(self):
        return self._status == self.DOWNLOADER_ERROR

    def getError(self):
        return self._error

    def cleanup(self):
        if self.isError() or self.isDownloaderError():
            self.setNone()


class ScheduledDownload(QtCore.QObject):
    enableChanged = QtCore.pyqtSignal()
    channelDataUpdateStarted = QtCore.pyqtSignal()
    channelDataUpdateFinished = QtCore.pyqtSignal()
    channelDataUpdated = QtCore.pyqtSignal()
    channelConnected = QtCore.pyqtSignal()
    downloaderCreated = QtCore.pyqtSignal(object, object)
    downloaderDestroyed = QtCore.pyqtSignal(object, object)

    STREAM_PREVIEW_IMAGE_URL_FORMAT = "https://static-cdn.jtvnw.net/previews-ttv/live_user_{login}-{{width}}x{{height}}.jpg"
    GAME_BOX_ART_URL_FORMAT = "https://static-cdn.jtvnw.net/ttv-boxart/{id}-{{width}}x{{height}}.jpg"

    def __init__(self, scheduledDownloadPreset, parent):
        super(ScheduledDownload, self).__init__(parent=parent)
        self.uuid = uuid.uuid4()
        self.preset = scheduledDownloadPreset
        self.channel = None
        self.channelDataUpdateThread = Utils.WorkerThread(
            target=Engine.Search.Channel,
            kwargs={
                "login": self.preset.channel
            },
            parent=self
        )
        self.channelDataUpdateThread.resultSignal.connect(self.channelDataUpdateResult)
        self.accessTokenThread = Utils.WorkerThread(parent=self)
        self.accessTokenThread.resultSignal.connect(self.processStreamAccessTokenResult)
        self.downloader = None
        self.status = ScheduledDownloadStatus(parent=self)
        self.updateChannelData()
        self.parent().enabledChangedSignal.connect(self.parentEnabledChanged)

    def setEnabled(self, enabled):
        self.preset.setEnabled(enabled)
        self.status.cleanup()
        self._syncEnabledState()
        self.enableChanged.emit()

    def isEnabled(self):
        return self.preset.isEnabled()

    def isParentEnabled(self):
        return self.parent().isEnabled()

    def isGloballyEnabled(self):
        return self.isParentEnabled() and self.isEnabled()

    def parentEnabledChanged(self, enabled):
        self._syncEnabledState()
        if enabled:
            self.updateChannelData()
        self.enableChanged.emit()

    def _syncEnabledState(self):
        if self.isChannelConnected():
            if self.isGloballyEnabled():
                self.startDownloadIfOnline()
            else:
                if self.status.isDownloading():
                    self.downloader.cancel()
                elif self.status.isError() or self.status.isDownloaderError():
                    self.status.setNone()

    def isChannelConnected(self):
        return self.channel != None

    def channelConnectedHandler(self):
        self.channelDataUpdateThread.setup(
            target=Engine.Search.Channel,
            kwargs={
                "id": str(self.channel.id)
            }
        )
        self.pubSubSubscriber = ScheduledDownloadPubSub.subscribe(self.channel.id, key=self.getId())
        self.pubSubSubscriber.eventReceived.connect(self.pubSubEventHandler)
        self._syncEnabledState()
        self.channelConnected.emit()

    def canStartDownload(self):
        return self.isGloballyEnabled() and self.isChannelConnected() and self.isOnline() and not self.status.isGeneratingAccessToken() and not self.status.isDownloading()

    def isUpdatingChannelData(self):
        return self.channelDataUpdateThread.isRunning()

    def updateChannelData(self):
        if not self.isUpdatingChannelData():
            self.channelDataUpdateStarted.emit()
            self.channelDataUpdateThread.start()

    def channelDataUpdateResult(self, result):
        if result.success:
            isFirstConnect = not self.isChannelConnected()
            self.channel = result.data
            self.channelDataUpdated.emit()
            if isFirstConnect:
                self.channelConnectedHandler()
            else:
                self.startDownloadIfOnline()
        self.channelDataUpdateFinished.emit()

    def setOnline(self):
        if self.isOffline():
            self.channel.stream = TwitchGqlModels.Stream({
                "title": self.channel.lastBroadcast.title,
                "previewImageURL": "" if self.channel.login == "" else self.STREAM_PREVIEW_IMAGE_URL_FORMAT.format(login=self.channel.login),
                "broadcaster": {
                    "id": self.channel.id,
                    "login": self.channel.login,
                    "displayName": self.channel.displayName
                }
            })
            self.channel.stream.game = self.channel.lastBroadcast.game
            self.channelDataUpdated.emit()

    def setOffline(self):
        if self.isOnline():
            self.channel.stream = None
            self.channelDataUpdated.emit()

    def isOnline(self):
        return self.channel.stream != None

    def isOffline(self):
        return not self.isOnline()

    def getStreamInfo(self):
        return self.channel.stream

    def pubSubEventHandler(self, event):
        topic, data = event.topic, event.data
        if topic.eventType == TwitchPubSubEvents.EventTypes.VideoPlaybackById:
            if data["type"] == "stream-up":
                self.setOnline()
                self.channel.stream.createdAt = QtCore.QDateTime.fromSecsSinceEpoch(data["server_time"], QtCore.Qt.UTC)
            elif data["type"] == "stream-down":
                self.setOffline()
            elif data["type"] == "viewcount":
                self.setOnline()
                self.channel.stream.viewersCount = data["viewers"]
            elif data["type"] == "commercial":
                pass
        elif topic.eventType == TwitchPubSubEvents.EventTypes.BroadcastSettingsUpdate:
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
            self.channel.lastBroadcast.game = TwitchGqlModels.Game(gameData)
            if self.isOnline():
                self.channel.stream.title = self.channel.lastBroadcast.title
                self.channel.stream.game = self.channel.lastBroadcast.game
        self.channelDataUpdated.emit()
        self.startDownloadIfOnline()

    def startDownloadIfOnline(self):
        if self.canStartDownload():
            self.generateStreamAccessToken()

    def generateStreamAccessToken(self):
        self.status.setGeneratingAccessToken()
        self.accessTokenThread.setup(
            target=AccessTokenGenerator.generateStreamAccessToken,
            args=(self.getStreamInfo(),)
        )
        self.accessTokenThread.start()

    def processStreamAccessTokenResult(self, result):
        if result.success:
            if self.isGloballyEnabled() and self.isOnline():
                stream = result.data
                try:
                    self.createDownloader(stream)
                except Exception as e:
                    self.status.setError(e)
            else:
                self.status.setNone()
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.ChannelIsOffline):
            self.setOffline()
            self.status.setNone()
        else:
            if self.isGloballyEnabled():
                self.status.setError(result.error)
            else:
                self.status.setNone()

    def createDownloader(self, accessToken):
        stream = self.getStreamInfo()
        downloadInfo = DownloadInfo(stream, accessToken)
        downloadInfo.setDirectory(self.preset.directory)
        selectedResolution = self.preset.selectResolution(accessToken.getResolutions())
        downloadInfo.setResolution(accessToken.getResolutions().index(selectedResolution))
        downloadInfo.setAbsoluteFileName(Utils.createUniqueFile(downloadInfo.directory, FileNameGenerator.generateFileName(stream, selectedResolution, customTemplate=self.preset.filenameTemplate), self.preset.fileFormat, exclude=FileNameManager.getLockedFileNames()))
        self.downloader = TwitchDownloader.create(downloadInfo, parent=self)
        self.downloader.finished.connect(self.downloadResultHandler)
        self.downloaderCreated.emit(self, self.downloader)
        self.status.setDownloading()
        self.downloader.start()

    def downloadResultHandler(self, downloader):
        error = self.downloader.status.getError()
        if error == None or not self.isGloballyEnabled():
            self.status.setNone()
        else:
            self.status.setDownloaderError(error)
        downloader.setParent(None)
        self.downloader = None
        self.downloaderDestroyed.emit(self, downloader)

    def getId(self):
        return self.uuid

    def __del__(self):
        if self.isChannelConnected():
            ScheduledDownloadPubSub.unsubscribe(self.channel.id, key=self.getId())


class _ScheduledDownloadManager(QtCore.QObject):
    enabledChangedSignal = QtCore.pyqtSignal(bool)
    createdSignal = QtCore.pyqtSignal(object)
    destroyedSignal = QtCore.pyqtSignal(object)
    downloaderCreatedSignal = QtCore.pyqtSignal(object, object)
    downloaderDestroyedSignal = QtCore.pyqtSignal(object, object)
    downloaderCountChangedSignal = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(_ScheduledDownloadManager, self).__init__(parent=parent)
        self._enabled = False
        self.scheduledDownloads = {}
        self.runningScheduledDownloads = []
        Updater.statusUpdated.connect(self._updatePubSubState)
        self._updatePubSubState()

    def setEnabled(self, enabled):
        self._enabled = enabled
        self._updatePubSubState()
        self.enabledChangedSignal.emit(self._enabled)

    def isEnabled(self):
        return self._enabled

    def _updatePubSubState(self):
        if Updater.status.isOperational() and self.isEnabled() and len(self.scheduledDownloads) != 0:
            if not ScheduledDownloadPubSub.isOpened():
                ScheduledDownloadPubSub.open()
        else:
            if ScheduledDownloadPubSub.isOpened():
                ScheduledDownloadPubSub.close()

    def setPresets(self, presetList):
        self.removeAll()
        for scheduledDownloadPreset in presetList:
            self.create(scheduledDownloadPreset)

    def getPresets(self):
        return [scheduledDownload.preset for scheduledDownload in self.getScheduledDownloads()]

    def create(self, scheduledDownloadPreset):
        scheduledDownload = ScheduledDownload(scheduledDownloadPreset, parent=self)
        scheduledDownload.downloaderCreated.connect(self.downloaderCreated)
        scheduledDownload.downloaderDestroyed.connect(self.downloaderDestroyed)
        scheduledDownloadId = scheduledDownload.getId()
        self.scheduledDownloads[scheduledDownloadId] = scheduledDownload
        self.createdSignal.emit(scheduledDownloadId)
        self._updatePubSubState()
        return scheduledDownloadId

    def downloaderCreated(self, scheduledDownload, downloader):
        FileNameManager.lock(downloader.setup.downloadInfo.getAbsoluteFileName())
        self.runningScheduledDownloads.append(scheduledDownload)
        self.downloaderCountChangedSignal.emit(len(self.getRunningDownloaders()))
        self.downloaderCreatedSignal.emit(scheduledDownload, downloader)

    def downloaderDestroyed(self, scheduledDownload, downloader):
        self.runningScheduledDownloads.remove(scheduledDownload)
        self.downloaderCountChangedSignal.emit(len(self.getRunningDownloaders()))
        FileNameManager.unlock(downloader.setup.downloadInfo.getAbsoluteFileName())
        self.downloaderDestroyedSignal.emit(scheduledDownload, downloader)

    def get(self, scheduledDownloadId):
        return self.scheduledDownloads[scheduledDownloadId]

    def remove(self, scheduledDownloadId):
        self.scheduledDownloads.pop(scheduledDownloadId).setParent(None)
        self.destroyedSignal.emit(scheduledDownloadId)
        self._updatePubSubState()

    def cancelAll(self):
        for downloader in self.getRunningDownloaders():
            downloader.cancel()

    def waitAll(self):
        for downloader in self.getRunningDownloaders():
            downloader.wait()

    def removeAll(self):
        self.cancelAll()
        self.waitAll()
        for scheduledDownloadId in [*self.getScheduledDownloadKeys()]:
            self.remove(scheduledDownloadId)

    def getScheduledDownloadKeys(self):
        return self.scheduledDownloads.keys()

    def getScheduledDownloads(self):
        return self.scheduledDownloads.values()

    def getRunningScheduledDownloads(self):
        return self.runningScheduledDownloads

    def getRunningDownloaders(self):
        return [scheduledDownloads.downloader for scheduledDownloads in self.getRunningScheduledDownloads()]

    def isDownloaderRunning(self):
        return len(self.getRunningDownloaders()) != 0

    def cleanup(self):
        if ScheduledDownloadPubSub.isOpened():
            ScheduledDownloadPubSub.close()

ScheduledDownloadManager = _ScheduledDownloadManager()