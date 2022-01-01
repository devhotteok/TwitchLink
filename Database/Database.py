from .EncoderDecoder import JsonDatabase, DatabaseEncoder, DatabaseDecoder
from .Loader import DatabaseLoader

from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Services.Utils.SystemUtils import SystemUtils
from Services.Utils.Image.Config import Config as ImageLoaderConfig
from Services.Account.Auth import TwitchAccount
from Services.Twitch.Playback.TwitchPlaybackAccessTokens import TwitchPlaybackAccessTokenTypes
from Services.Translator.Translator import Translator
from Download.Downloader.Task.ThreadPool import ThreadPool
from Download.Downloader.Task.Config import Config as TaskConfig

import os

from datetime import datetime


class TermsOfService:
    def __init__(self):
        self._agreedTime = None

    def agree(self):
        self._agreedTime = datetime.now()

    def getAgreedTime(self):
        return self._agreedTime

class Account:
    def __init__(self):
        self._user = TwitchAccount()

    def login(self):
        self._user.login()

    def logout(self):
        self._user.logout()

    def updateAccount(self):
        self._user.updateAccount()

    def isUserLoggedIn(self):
        return self._user.connected

    def getAccountData(self):
        return self._user.data

    def checkAuthToken(self):
        self._user.checkToken()

    def getAuthToken(self):
        return self._user.token

class General:
    def __init__(self):
        self._autoClose = False
        self._bookmarks = []

    def setAutoCloseEnabled(self, autoClose):
        self._autoClose = autoClose

    def setBookmarks(self, bookmarks):
        self._bookmarks = bookmarks

    def isAutoCloseEnabled(self):
        return self._autoClose

    def getBookmarks(self):
        return self._bookmarks

class Templates:
    def __init__(self):
        self._streamFilename = "[{type}] [{channel_name}] [{date}] {title} {resolution}"
        self._videoFilename = "[{type}] [{channel_name}] [{date}] {title} {resolution}"
        self._clipFilename = "[{type}] [{channel_name}] {title}"

    def setStreamFilename(self, streamFilename):
        self._streamFilename = streamFilename

    def setVideoFilename(self, videoFilename):
        self._videoFilename = videoFilename

    def setClipFilename(self, clipFilename):
        self._clipFilename = clipFilename

    def getStreamFilename(self):
        return self._streamFilename

    def getVideoFilename(self):
        return self._videoFilename

    def getClipFilename(self):
        return self._clipFilename

class Localization:
    def __init__(self):
        self.setLanguage(Translator.getDefaultLanguage())
        self.setTimezoneNo(SystemUtils.getTimezoneList().index(SystemUtils.getLocalTimezone(preferredTimezones=[Translator.getLanguageData()[language]["preferredTimezone"] for language in Translator.getLanguageKeyList()])))

    def setLanguage(self, language):
        self._language = language
        self.reloadTranslator()

    def setTimezoneNo(self, timezoneNo):
        self._timezoneNo = timezoneNo
        self._timezone = SystemUtils.getTimezone(SystemUtils.getTimezoneList()[timezoneNo])

    def reloadTranslator(self):
        Translator.setLanguage(self._language)

    def getLanguage(self):
        return self._language

    def getTimezoneIndex(self):
        return self._timezoneNo

    def getTimezone(self):
        return self._timezone

    def getTimezoneList(self):
        return SystemUtils.getTimezoneList()

class Temp:
    def __init__(self):
        self._defaultDirectory = Config.DEFAULT_FILE_DIRECTORY
        self._defaultFormat = {
            TwitchPlaybackAccessTokenTypes.TYPES.STREAM: "ts",
            TwitchPlaybackAccessTokenTypes.TYPES.VIDEO: "ts",
            TwitchPlaybackAccessTokenTypes.TYPES.CLIP: "mp4",
            ImageLoaderConfig.IMAGE_DATA_TYPE: "jpg"
        }
        self._windowGeometry = {}

    def setDefaultDirectory(self, defaultDirectory):
        self._defaultDirectory = defaultDirectory

    def setDefaultFormat(self, contentType, defaultFormat):
        self._defaultFormat[contentType] = defaultFormat

    def setWindowGeometry(self, windowName, windowGeometry):
        self._windowGeometry[windowName] = windowGeometry

    def updateDefaultDirectory(self):
        for directory in [Config.DEFAULT_FILE_DIRECTORY, Config.APPDATA_PATH]:
            try:
                OSUtils.createDirectory(self.getDefaultDirectory())
                break
            except:
                self.setDefaultDirectory(directory)

    def getDefaultDirectory(self):
        return self._defaultDirectory

    def getDefaultFormat(self, contentType):
        return self._defaultFormat[contentType]

    def getWindowGeometry(self, windowName):
        return self._windowGeometry.get(windowName)

class Download:
    def __init__(self):
        self._downloadSpeed = TaskConfig.RECOMMENDED_THREAD_LIMIT
        self._unmuteVideo = True
        self._updateTrack = False

    def setDownloadSpeed(self, downloadSpeed):
        self._downloadSpeed = downloadSpeed
        self.reloadDownloadSpeed()

    def setUnmuteVideoEnabled(self, unmuteVideo):
        self._unmuteVideo = unmuteVideo

    def setUpdateTrackEnabled(self, updateTrack):
        self._updateTrack = updateTrack

    def reloadDownloadSpeed(self):
        ThreadPool.setMaxThreadCount(self._downloadSpeed)

    def getDownloadSpeed(self):
        return self._downloadSpeed

    def isUnmuteVideoEnabled(self):
        return self._unmuteVideo

    def isUpdateTrackEnabled(self):
        return self._updateTrack


class Database:
    def __init__(self):
        self.version = Config.VERSION
        self.load()

    def open(self):
        try:
            with open(Config.DB_FILE, "r", encoding="utf-8") as file:
                return JsonDatabase.load(file, cls=DatabaseDecoder)
        except:
            self.save()
            return {}

    def load(self):
        self.resetData()
        DatabaseLoader.load(self, self.open())
        self.localization.reloadTranslator()
        self.download.reloadDownloadSpeed()

    def save(self):
        try:
            OSUtils.createDirectory(Config.DB_ROOT)
            with open(Config.DB_FILE, "w", encoding="utf-8") as file:
                JsonDatabase.dump(DatabaseLoader.unpack(self.__dict__), file, cls=DatabaseEncoder)
        except:
            return False
        else:
            return True

    def resetData(self):
        self.termsOfService = TermsOfService()
        self.account = Account()
        self.general = General()
        self.templates = Templates()
        self.localization = Localization()
        self.temp = Temp()
        self.download = Download()

    def reset(self):
        self.resetData()
        self.save()

    def saveLogs(self, logs):
        try:
            if not os.path.exists(Config.DOWNLOAD_LOGS):
                with open(Config.DOWNLOAD_LOGS, "w", encoding="utf-8") as file:
                    file.write("{} Download Logs".format(Config.APP_NAME))
            with open(Config.DOWNLOAD_LOGS, "a", encoding="utf-8") as file:
                file.write("\n\n{}".format(logs))
        except:
            return False
        else:
            return True

DB = Database()