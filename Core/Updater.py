from Core.Config import Config
from Services.NetworkRequests import Network
from Services.Utils.OSUtils import OSUtils
from Services.ContentManager import ContentManager
from Services.Translator.Translator import Translator
from Services.Document import DocumentData, DocumentButtonData

from PyQt5 import QtCore


class Exceptions:
    class ConnectionFailure(Exception):
        def __str__(self):
            return "Connection Failure"

    class UnexpectedError(Exception):
        def __str__(self):
            return "Unexpected Error"

    class Unavailable(Exception):
        def __str__(self):
            return "Unavailable"

    class UpdateRequired(Exception):
        def __str__(self):
            return "Update Required"

    class UpdateFound(Exception):
        def __str__(self):
            return "Update Found"


class _Status:
    CONNECTION_FAILURE = 0
    UNEXPECTED_ERROR = 1
    UNAVAILABLE = 2
    UPDATE_REQUIRED = 3
    UPDATE_FOUND = 4
    AVAILABLE = 5


    class Version:
        def __init__(self, data):
            self.latestVersion = data.get("latestVersion")
            self.updateRequired = not Config.VERSION in data.get("compatibleVersions", []) and self.latestVersion != Config.VERSION
            updateNoteData = data.get("updateNote", {}).get(Translator.getLanguage(), {})
            self.updateNote = updateNoteData.get("content")
            self.updateNoteType = updateNoteData.get("contentType")
            self.updateUrl = data.get("updateUrl", Config.HOMEPAGE_URL)

    def __init__(self):
        self.setStatus(self.UNAVAILABLE)
        self.updateStatusData({})
        self.updateNotifications({})

    def updateStatusData(self, data):
        self.operational = data.get("operational", False)
        operationalInfoData = data.get("operationalInfo", {}).get(Translator.getLanguage(), {})
        self.operationalInfo = operationalInfoData.get("content")
        self.operationalInfoType = operationalInfoData.get("contentType")
        self.version = self.Version(data.get("version", {}))

    def updateNotifications(self, data):
        self.notifications = [
            DocumentData(
                contentId=notification.get("contentId", None),
                contentVersion=notification.get("contentVersion", 0),
                title=notification.get("title", ""),
                content=notification.get("content", ""),
                contentType=notification.get("contentType", ""),
                modal=notification.get("modal", False),
                blockExpiry=notification.get("blockExpiry", False),
                buttons=[
                    DocumentButtonData(
                        text=button.get("text", ""),
                        action=button.get("action", None),
                        role=button.get("role", "accept"),
                        default=button.get("default", False)
                    ) for button in notification.get("buttons", [])
                ]
            ) for notification in data.get(Translator.getLanguage(), [])
        ]

    def setStatus(self, appStatus):
        self.appStatus = appStatus

    def getStatus(self):
        return self.appStatus

    def isOperational(self):
        return self.appStatus == self.UPDATE_FOUND or self.appStatus == self.AVAILABLE


class _Updater(QtCore.QObject):
    updateProgress = QtCore.pyqtSignal(int)
    updateComplete = QtCore.pyqtSignal()

    MAX_REDIRECT_COUNT = 10
    TOTAL_TASK_COUNT = 4

    def __init__(self, parent=None):
        super(_Updater, self).__init__(parent=parent)
        self.status = _Status()

    def update(self):
        try:
            self.updateProgress.emit(0)
            try:
                self.updateStatus()
            except Exceptions.Unavailable:
                self.status.setStatus(self.status.UNAVAILABLE)
            except Exceptions.UpdateFound:
                self.status.setStatus(self.status.UPDATE_FOUND)
            else:
                self.status.setStatus(self.status.AVAILABLE)
            self.updateProgress.emit(1)
            self.updateNotifications()
            self.updateProgress.emit(2)
            self.updateConfig()
            self.updateProgress.emit(3)
            self.updateRestrictions()
            self.updateProgress.emit(4)
        except Exceptions.ConnectionFailure:
            self.status.setStatus(self.status.CONNECTION_FAILURE)
        except Exceptions.UnexpectedError:
            self.status.setStatus(self.status.UNEXPECTED_ERROR)
        except:
            self.status.setStatus(self.status.UPDATE_REQUIRED)
        self.updateComplete.emit()

    def getData(self, url):
        for requestCount in range(self.MAX_REDIRECT_COUNT + 1):
            try:
                response = Network.session.get(OSUtils.joinUrl(url, params={"version": Config.VERSION}))
                if response.status_code == 200:
                    if response.text.startswith("redirect:"):
                        url = response.text.split(":", 1)[1]
                    else:
                        return response
                else:
                    raise
            except:
                break
        raise Exceptions.ConnectionFailure

    def updateStatus(self):
        response = self.getData(OSUtils.joinUrl(Config.SERVER_URL, "status.json"))
        try:
            data = response.json()
            self.status.updateStatusData(data)
        except:
            raise Exceptions.UpdateRequired
        if self.status.operational:
            if self.status.version.latestVersion != Config.VERSION:
                if self.status.version.updateRequired:
                    raise Exceptions.UpdateRequired
                else:
                    raise Exceptions.UpdateFound
        else:
            raise Exceptions.Unavailable

    def updateNotifications(self):
        response = self.getData(OSUtils.joinUrl(Config.SERVER_URL, "notifications.json"))
        try:
            data = response.json()
            self.status.updateNotifications(data)
        except:
            raise Exceptions.UnexpectedError

    def updateConfig(self):
        response = self.getData(OSUtils.joinUrl(Config.SERVER_URL, "config.json"))
        try:
            from Core.Config import Config as CoreConfig
            from Services.Image.Config import Config as ImageConfig
            from Services.Account.Config import Config as AuthConfig
            from Services.Ad.Config import Config as AdConfig
            from Services.Translator.Config import Config as TranslatorConfig
            from Services.Temp.Config import Config as TempConfig
            from Services.Logging.Config import Config as LogConfig
            from Services.Twitch.Gql.TwitchGqlConfig import Config as GqlConfig
            from Services.Twitch.Playback.TwitchPlaybackConfig import Config as PlaybackConfig
            from Search.Config import Config as SearchConfig
            from Search.Helper.Config import Config as SearchHelperConfig
            from Download.Downloader.Engine.Config import Config as DownloadEngineConfig
            from Download.Downloader.FFmpeg.Config import Config as FFmpegConfig
            CONFIG_FILES = {
                "": CoreConfig,
                "IMAGE": ImageConfig,
                "AUTH": AuthConfig,
                "AD": AdConfig,
                "TRANSLATOR": TranslatorConfig,
                "TEMP": TempConfig,
                "LOG": LogConfig,
                "API": GqlConfig,
                "PLAYBACK": PlaybackConfig,
                "SEARCH": SearchConfig,
                "SEARCH_HELPER": SearchHelperConfig,
                "DOWNLOAD_ENGINE": DownloadEngineConfig,
                "FFMPEG": FFmpegConfig
            }
            data = response.json()
            configData = data.get("global")
            configData.update(data.get("local").get(Translator.getLanguage()))
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
            raise Exceptions.UnexpectedError

    def updateRestrictions(self):
        response = self.getData(OSUtils.joinUrl(Config.SERVER_URL, "restrictions.json"))
        try:
            data = response.json()
            ContentManager.setRestrictions(data)
        except:
            raise Exceptions.UnexpectedError

Updater = _Updater()