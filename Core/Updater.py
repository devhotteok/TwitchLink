from Core import App
from Core.GlobalExceptions import Exceptions
from Core.Config import Config
from Services.Utils.Utils import Utils

from PyQt6 import QtCore, QtNetwork

import enum
import re
import json


class Version:
    REGEX = re.compile("(\d+)\.(\d+)(?:\.(\d+)((?:\-|\+)\S+)?)?")
    def __init__(self, version: str):
        versionData = re.search(self.REGEX, version)
        if versionData == None:
            self.major = 0
            self.minor = 0
            self.patch = 0
            self.data = None
        else:
            self.major = int(versionData.group(1))
            self.minor = int(versionData.group(2))
            self.patch = int(versionData.group(3) or 0)
            self.data = versionData.group(4)

    def __lt__(self, other):
        return (self.major, self.minor, self.patch) < (other.major, other.minor, other.patch)

    def __le__(self, other):
        return (self.major, self.minor, self.patch) <= (other.major, other.minor, other.patch)

    def __gt__(self, other):
        return (self.major, self.minor, self.patch) > (other.major, other.minor, other.patch)

    def __ge__(self, other):
        return (self.major, self.minor, self.patch) >= (other.major, other.minor, other.patch)

    def __eq__(self, other):
        if isinstance(other, Version):
            return (self.major, self.minor, self.patch) == (other.major, other.minor, other.patch)
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, Version):
            return (self.major, self.minor, self.patch) != (other.major, other.minor, other.patch)
        else:
            return NotImplemented

    def __str__(self):
        return f"{self.major}.{self.minor}.{self.patch}{'' if self.data == None else self.data}"


class VersionInfo:
    def __init__(self, data: dict):
        self.latestVersion = Version(data.get("latestVersion", ""))
        self.requiredVersion = Version(data.get("requiredVersion", ""))
        self.appVersion = Version(Config.APP_VERSION)
        updateNoteData = data.get("updateNote", {}).get(App.Translator.getLanguage(), {})
        self.updateNote = updateNoteData.get("content")
        self.updateNoteType = updateNoteData.get("contentType")
        self.updateUrl = data.get("updateUrl", Config.HOMEPAGE_URL)

    def isLatestVersion(self) -> bool:
        return self.appVersion == self.latestVersion

    def hasUpdate(self) -> bool:
        return self.appVersion < self.latestVersion

    def isUpdateRequired(self) -> bool:
        return self.appVersion < self.requiredVersion


class Status:
    class Types(enum.Enum):
        NONE = -1
        CONNECTION_FAILURE = 0
        UNEXPECTED_ERROR = 1
        SESSION_EXPIRED = 2
        UNAVAILABLE = 3
        UPDATE_REQUIRED = 4
        UPDATE_FOUND = 5
        AVAILABLE = 6

    def __init__(self):
        self._status = self.Types.NONE
        self.networkErrorCount = 0
        self.update({})

    def update(self, data: dict) -> None:
        self.session = data.get("session", None)
        self.sessionStrict = data.get("sessionStrict", True)
        self.operational = data.get("operational", False)
        operationalInfoData = data.get("operationalInfo", {}).get(App.Translator.getLanguage(), {})
        self.operationalInfo = operationalInfoData.get("content", "")
        self.operationalInfoType = operationalInfoData.get("contentType", "")
        self.versionInfo = VersionInfo(data.get("version", {}))

    def setStatus(self, status: Types) -> None:
        if self.getStatus() != self.Types.NONE and status in (self.Types.CONNECTION_FAILURE, self.Types.UNEXPECTED_ERROR) and self.networkErrorCount < Config.STATUS_UPDATE_NETWORK_ERROR_MAX_IGNORE_COUNT:
            self.networkErrorCount += 1
        else:
            self.networkErrorCount = 0
            self._status = status

    def getStatus(self) -> Types:
        return self._status

    def isOperational(self) -> bool:
        return self.getStatus() == self.Types.UPDATE_FOUND or self.getStatus() == self.Types.AVAILABLE


class DataLoader(QtCore.QObject):
    dataLoaded = QtCore.pyqtSignal(object)
    errorOccurred = QtCore.pyqtSignal(Exception)

    def __init__(self, url: str, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._redirectCount = 0
        self._sendRequest(url)

    def _sendRequest(self, url: str) -> None:
        url = QtCore.QUrl(url)
        query = QtCore.QUrlQuery()
        for key, value in {
            "version": Config.APP_VERSION,
            "user": "" if App.Account.user == None else App.Account.user.id
        }.items():
            query.addQueryItem(key, value if isinstance(value, str) else json.dumps(value))
        url.setQuery(query)
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(url))
        request.setAttribute(QtNetwork.QNetworkRequest.Attribute.CacheLoadControlAttribute, QtNetwork.QNetworkRequest.CacheLoadControl.AlwaysNetwork)
        self._networkReply = App.NetworkAccessManager.get(request)
        self._networkReply.finished.connect(self._finished)

    def _finished(self) -> None:
        if self._networkReply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            try:
                text = self._networkReply.readAll().data().decode(errors="ignore")
                if text.startswith("redirect:"):
                    if self._redirectCount < Config.STATUS_UPDATE_MAX_REDIRECT_COUNT:
                        self._redirectCount += 1
                        self._sendRequest(text.split(":", 1)[1])
                    else:
                        self._raiseException(Exceptions.UnexpectedError())
                else:
                    data = json.loads(text)
                    self.dataLoaded.emit(data)
                    self.deleteLater()
            except:
                self._raiseException(Exceptions.UnexpectedError())
        else:
            self._raiseException(Exceptions.NetworkError(self._networkReply))

    def _raiseException(self, exception: Exception) -> None:
        self.errorOccurred.emit(exception)
        self.deleteLater()


class Updater(QtCore.QObject):
    updateProgress = QtCore.pyqtSignal(int)
    updateComplete = QtCore.pyqtSignal()
    statusUpdated = QtCore.pyqtSignal()
    configUpdated = QtCore.pyqtSignal()

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.status = Status()
        self._tempStatus: Status | None = None
        self._autoUpdateEnabled = False
        self._updateTimer = QtCore.QTimer(parent=self)
        self._updateTimer.setSingleShot(True)
        self._updateTimer.timeout.connect(self.update)
        self.updateComplete.connect(self._updateCompleteHandler)
        self.configUpdated.connect(self.configUpdateHandler)
        self.configUpdateHandler()

    def configUpdateHandler(self) -> None:
        self._updateTimer.setInterval(Config.STATUS_UPDATE_INTERVAL)

    def startAutoUpdate(self) -> None:
        if not self._autoUpdateEnabled:
            self._autoUpdateEnabled = True
            self._updateTimer.start()

    def stopAutoUpdate(self) -> None:
        if self._autoUpdateEnabled:
            self._autoUpdateEnabled = False
            self._updateTimer.stop()

    def _updateCompleteHandler(self) -> None:
        if self._autoUpdateEnabled:
            self._updateTimer.start()

    def _handleNetworkException(self, exception: Exception) -> None:
        if isinstance(exception, Exceptions.NetworkError):
            self._finishUpdate(Status.Types.CONNECTION_FAILURE)
        else:
            self._finishUpdate(Status.Types.UNEXPECTED_ERROR)

    def _finishUpdate(self, status: Status.Types) -> None:
        self._tempStatus.setStatus(status)
        if self.status.getStatus() != self._tempStatus.getStatus():
            self.status = self._tempStatus
            self.statusUpdated.emit()
        else:
            self.status = self._tempStatus
        self._tempStatus = None
        self.updateComplete.emit()

    def update(self) -> None:
        self._tempStatus = Status()
        self._tempStatus._status = self.status.getStatus()
        self.updateStatus()

    def updateStatus(self) -> None:
        self.updateProgress.emit(0)
        dataLoader = DataLoader(Utils.joinUrl(Config.SERVER_URL, "status.json"), parent=self)
        dataLoader.errorOccurred.connect(self._handleNetworkException)
        dataLoader.dataLoaded.connect(self._statusDataHandler)

    def _statusDataHandler(self, data: dict) -> None:
        try:
            self._tempStatus.update(data)
        except Exceptions.UnexpectedError:
            self._finishUpdate(Status.Types.UNEXPECTED_ERROR)
        except:
            self._finishUpdate(Status.Types.UPDATE_REQUIRED)
        else:
            if self._tempStatus.sessionStrict:
                if self.status.session != self._tempStatus.session and self.status.session != None and self._tempStatus.session != None:
                    self._finishUpdate(Status.Types.SESSION_EXPIRED)
                    return
            if not self._tempStatus.operational:
                self._finishUpdate(Status.Types.UNAVAILABLE)
                return
            if self._tempStatus.versionInfo.hasUpdate():
                if self._tempStatus.versionInfo.isUpdateRequired():
                    self._finishUpdate(Status.Types.UPDATE_REQUIRED)
                    return
            self.updateNotifications()

    def updateNotifications(self) -> None:
        self.updateProgress.emit(1)
        dataLoader = DataLoader(Utils.joinUrl(Config.SERVER_URL, "notifications.json"), parent=self)
        dataLoader.errorOccurred.connect(self._handleNetworkException)
        dataLoader.dataLoaded.connect(self._notificationsDataHandler)

    def _notificationsDataHandler(self, data: dict) -> None:
        try:
            App.Notifications.updateNotifications(data)
        except:
            self._finishUpdate(Status.Types.UNEXPECTED_ERROR)
        else:
            self.updateConfig()

    def updateConfig(self) -> None:
        self.updateProgress.emit(2)
        dataLoader = DataLoader(Utils.joinUrl(Config.SERVER_URL, "config.json"), parent=self)
        dataLoader.errorOccurred.connect(self._handleNetworkException)
        dataLoader.dataLoaded.connect(self._configDataHandler)

    def _configDataHandler(self, data: dict) -> None:
        try:
            from Core.Config import Config as CoreConfig
            from Services.Image.Config import Config as ImageConfig
            from Services.Account.Config import Config as AuthConfig
            from Services.PartnerContent.Config import Config as PartnerContentConfig
            from Services.Translator.Config import Config as TranslatorConfig
            from Services.Temp.Config import Config as TempConfig
            from Services.Logging.Config import Config as LogConfig
            from Services.Twitch.Authentication.Integrity.IntegrityConfig import Config as IntegrityConfig
            from Services.Twitch.GQL.TwitchGQLConfig import Config as GQLConfig
            from Services.Twitch.Playback.TwitchPlaybackConfig import Config as PlaybackConfig
            from Services.Twitch.PubSub.TwitchPubSubConfig import Config as PubSubConfig
            from Search.Config import Config as SearchConfig
            from Search.Helper.Config import Config as SearchHelperConfig
            from Download.Downloader.Core.Engine.Config import Config as DownloadConfig
            from Download.Downloader.Core.Engine.FFmpeg import Config as FFmpegConfig
            CONFIG_FILES = {
                "": CoreConfig,
                "IMAGE": ImageConfig,
                "AUTH": AuthConfig,
                "PARTNER_CONTENT": PartnerContentConfig,
                "TRANSLATOR": TranslatorConfig,
                "TEMP": TempConfig,
                "LOG": LogConfig,
                "INTEGRITY": IntegrityConfig,
                "GQL": GQLConfig,
                "PLAYBACK": PlaybackConfig,
                "PUBSUB": PubSubConfig,
                "SEARCH": SearchConfig,
                "SEARCH_HELPER": SearchHelperConfig,
                "DOWNLOAD": DownloadConfig,
                "FFMPEG": FFmpegConfig
            }
            configData = data.get("global", {})
            configData.update(data.get("local", {}).get(App.Translator.getLanguage(), {}))
            for key, value in configData.items():
                if ":" in key:
                    configTarget, configPath = key.split(":", 1)
                    configTarget = CONFIG_FILES[configTarget]
                else:
                    configPath = key
                    configTarget = CONFIG_FILES[""]
                configPath = configPath.split(".")
                for target in configPath[:-1]:
                    configTarget = getattr(configTarget, target)
                setattr(configTarget, configPath[-1], value)
        except:
            self._finishUpdate(Status.Types.UNEXPECTED_ERROR)
        else:
            self.configUpdated.emit()
            self.updateRestrictions()

    def updateRestrictions(self) -> None:
        self.updateProgress.emit(3)
        dataLoader = DataLoader(Utils.joinUrl(Config.SERVER_URL, "restrictions.json"), parent=self)
        dataLoader.errorOccurred.connect(self._handleNetworkException)
        dataLoader.dataLoaded.connect(self._restrictionsDataHandler)

    def _restrictionsDataHandler(self, data: dict) -> None:
        try:
            App.ContentManager.setRestrictions(data)
        except:
            self._finishUpdate(Status.Types.UNEXPECTED_ERROR)
        else:
            if self._tempStatus.versionInfo.hasUpdate():
                self._finishUpdate(Status.Types.UPDATE_FOUND)
            else:
                self._finishUpdate(Status.Types.AVAILABLE)