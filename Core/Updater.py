from Core.Config import Config
from Services.NetworkRequests import requests
from Services.Utils.OSUtils import OSUtils
from Services.ContentManager import ContentManager
from Services.Translator.Translator import Translator


class Exceptions:
    class ConnectionFailure(Exception):
        def __str__(self):
            return "Connection Failure"
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
    UNAVAILABLE = 1
    UPDATE_REQUIRED = 2
    UPDATE_FOUND = 3
    AVAILABLE = 4

    class Notice:
        def __init__(self, data):
            self.message = data.get("message")
            self.url = data.get("url")

    class Version:
        def __init__(self, data):
            self.latestVersion = data.get("latestVersion")
            self.updateRequired = not Config.VERSION in data.get("compatibleVersions", []) and self.latestVersion != Config.VERSION
            self.updateNote = data.get("updateNote", {}).get(Translator.getLanguage())
            self.updateUrl = data.get("updateUrl", Config.HOMEPAGE_URL)

    def __init__(self):
        self.setStatus(self.UNAVAILABLE)
        self.syncData({})

    def syncData(self, data):
        self.operational = data.get("operational", False)
        self.notice = self.Notice(data.get("notice", {}).get(Translator.getLanguage(), {}))
        self.version = self.Version(data.get("version", {}))

    def setStatus(self, appStatus):
        self.appStatus = appStatus

    def getStatus(self):
        return self.appStatus

    def isRunnable(self):
        return self.appStatus == self.UPDATE_FOUND or self.appStatus == self.AVAILABLE


class _Updater:
    def __init__(self):
        self.status = _Status()

    def update(self):
        try:
            yield 0
            try:
                self.updateStatus()
            except Exceptions.Unavailable:
                self.status.setStatus(self.status.UNAVAILABLE)
            except Exceptions.UpdateFound:
                self.status.setStatus(self.status.UPDATE_FOUND)
            else:
                self.status.setStatus(self.status.AVAILABLE)
            yield 1
            self.updateConfig()
            yield 2
            self.updateRestrictions()
        except Exceptions.ConnectionFailure:
            self.status.setStatus(self.status.CONNECTION_FAILURE)
        except:
            self.status.setStatus(self.status.UPDATE_REQUIRED)

    def updateStatus(self):
        try:
            response = requests.get(OSUtils.joinUrl(Config.SERVER_URL, "status.json"))
        except:
            raise Exceptions.ConnectionFailure
        if response.status_code == 200:
            try:
                data = response.json()
                self.status.syncData(data)
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
        else:
            raise Exceptions.ConnectionFailure

    def updateConfig(self):
        try:
            response = requests.get(OSUtils.joinUrl(Config.SERVER_URL, "config.json"))
        except:
            raise Exceptions.ConnectionFailure
        if response.status_code == 200:
            try:
                from Core.Config import Config as CoreConfig
                from Services.Utils.Image.Config import Config as ImageLoaderConfig
                from Services.Account.Config import Config as AuthConfig
                from Services.Ad.Config import Config as AdConfig
                from Services.Translator.Config import Config as TranslatorConfig
                from Services.Temp.Config import Config as TempConfig
                from Services.Twitch.Gql.TwitchGqlConfig import Config as GqlConfig
                from Services.Twitch.Playback.TwitchPlaybackConfig import Config as PlaybackConfig
                from Search.Config import Config as SearchConfig
                from Search.Helper.Config import Config as SearchHelperConfig
                from Download.Downloader.Engine.Config import Config as DownloadEngineConfig
                from Download.Downloader.FFmpeg.Config import Config as FFmpegConfig
                from Download.Downloader.Task.Config import Config as TaskConfig
                CONFIG_FILES = {
                    "": CoreConfig,
                    "IMAGE_LOADER": ImageLoaderConfig,
                    "AUTH": AuthConfig,
                    "AD": AdConfig,
                    "TRANSLATOR": TranslatorConfig,
                    "TEMP": TempConfig,
                    "API": GqlConfig,
                    "PLAYBACK": PlaybackConfig,
                    "SEARCH": SearchConfig,
                    "SEARCH_HELPER": SearchHelperConfig,
                    "DOWNLOAD_ENGINE": DownloadEngineConfig,
                    "FFMPEG": FFmpegConfig,
                    "TASK": TaskConfig
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
                raise Exceptions.UpdateRequired
        else:
            raise Exceptions.ConnectionFailure

    def updateRestrictions(self):
        try:
            response = requests.get(OSUtils.joinUrl(Config.SERVER_URL, "restrictions.json"))
        except:
            raise Exceptions.ConnectionFailure
        if response.status_code == 200:
            try:
                data = response.json()
                ContentManager.setRestrictions(data)
            except:
                raise Exceptions.UpdateRequired
        else:
            raise Exceptions.ConnectionFailure

Updater = _Updater()