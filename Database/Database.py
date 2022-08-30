from .EncoderDecoder import Codable, Encoder, Decoder
from .Updater import Updaters

from Core.App import App
from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Services.Utils.SystemUtils import SystemUtils
from Services.Image.Loader import ImageLoader
from Services.Image.Config import Config as ImageConfig
from Services.Account.TwitchAccount import TwitchAccount
from Services.Twitch.Playback.TwitchPlaybackAccessTokens import TwitchPlaybackAccessTokenTypes
from Services.Translator.Translator import Translator
from Download import DownloadOptionHistory
from Download.Downloader.Engine.ThreadPool import ThreadPool as DownloadThreadPool
from Download.Downloader.Engine.Config import Config as EngineConfig

from PyQt5 import QtCore

import json


class Setup(Codable):
    def __init__(self):
        self._needSetup = True
        self._termsOfServiceAgreement = None

    def setupComplete(self):
        self._needSetup = False

    def needSetup(self):
        return self._needSetup

    def agreeTermsOfService(self):
        self._termsOfServiceAgreement = QtCore.QDateTime.currentDateTimeUtc()

    def getTermsOfServiceAgreement(self):
        return self._termsOfServiceAgreement

class Account(Codable):
    def __init__(self):
        self._user = TwitchAccount()

    def login(self, username, token, expiry):
        self._user.login(username, token, expiry)

    def logout(self):
        self._user.logout()

    def updateAccount(self):
        self._user.updateAccount()

    def isUserLoggedIn(self):
        return self._user.isConnected()

    def getAccountData(self):
        return self._user.data

    def checkAuthToken(self):
        self._user.checkToken()

    def getAuthToken(self):
        return self._user.token

class General(Codable):
    def __init__(self):
        self._openProgressWindow = True
        self._notify = True
        self._confirmExit = True
        self._bookmarks = []

    def setOpenProgressWindowEnabled(self, openProgressWindow):
        self._openProgressWindow = openProgressWindow

    def setNotifyEnabled(self, notify):
        self._notify = notify

    def setConfirmExitEnabled(self, confirmExit):
        self._confirmExit = confirmExit

    def setBookmarks(self, bookmarks):
        self._bookmarks = bookmarks

    def isOpenProgressWindowEnabled(self):
        return self._openProgressWindow

    def isNotifyEnabled(self):
        return self._notify

    def isConfirmExitEnabled(self):
        return self._confirmExit

    def getBookmarks(self):
        return self._bookmarks

class Templates(Codable):
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

class Advanced(Codable):
    def __init__(self):
        self._searchExternalContent = True
        self.setCachingEnabled(False)

    def __setup__(self):
        self.reloadCaching()

    def setSearchExternalContentEnabled(self, enabled):
        self._searchExternalContent = enabled

    def setCachingEnabled(self, enabled):
        self._caching = enabled
        self.reloadCaching()

    def reloadCaching(self):
        ImageLoader.setCachingEnabled(self._caching)

    def isSearchExternalContentEnabled(self):
        return self._searchExternalContent

    def isCachingEnabled(self):
        return self._caching

class Localization(Codable):
    def __init__(self):
        self.setLanguage(Translator.getDefaultLanguage())
        self._timezone = SystemUtils.getLocalTimezone()

    def __setup__(self):
        self.reloadTranslator()

    def setLanguage(self, language):
        self._language = language
        self.reloadTranslator()

    def setTimezone(self, timezone):
        self._timezone = SystemUtils.getTimezone(timezone)

    def reloadTranslator(self):
        Translator.setLanguage(self._language)

    def getLanguage(self):
        return self._language

    def getTimezone(self):
        return self._timezone

    def getTimezoneNameList(self):
        return SystemUtils.getTimezoneNameList()

class Temp(Codable):
    def __init__(self):
        self._downloadHistory = []
        self._downloadOptionHistory = {
            TwitchPlaybackAccessTokenTypes.STREAM: DownloadOptionHistory.StreamHistory(),
            TwitchPlaybackAccessTokenTypes.VIDEO: DownloadOptionHistory.VideoHistory(),
            TwitchPlaybackAccessTokenTypes.CLIP: DownloadOptionHistory.ClipHistory(),
            ImageConfig.DATA_TYPE: DownloadOptionHistory.ThumbnailHistory()
        }
        self._downloadStats = {
            "totalFiles": 0,
            "totalByteSize": 0
        }
        self._windowGeometry = {}
        self._blockedContent = {}

    def getDownloadHistory(self):
        return self._downloadHistory

    def addDownloadHistory(self, downloadHistory):
        self._downloadHistory.append(downloadHistory)

    def removeDownloadHistory(self, downloadHistory):
        self._downloadHistory.remove(downloadHistory)

    def getDownloadOptionHistory(self, contentType):
        return self._downloadOptionHistory[contentType]

    def updateDownloadStats(self, fileSize):
        self._downloadStats["totalFiles"] += 1
        self._downloadStats["totalByteSize"] += fileSize

    def getDownloadStats(self):
        return self._downloadStats

    def hasWindowGeometry(self, windowName):
        return windowName in self._windowGeometry

    def setWindowGeometry(self, windowName, windowGeometry):
        self._windowGeometry[windowName] = windowGeometry

    def getWindowGeometry(self, windowName):
        return self._windowGeometry[windowName]

    def isContentBlocked(self, contentId, contentVersion):
        if contentId in self._blockedContent:
            oldContentVersion, blockExpiry = self._blockedContent[contentId]
            if contentVersion != oldContentVersion or (blockExpiry != None and blockExpiry < QtCore.QDateTime.currentDateTimeUtc()):
                del self._blockedContent[contentId]
                return False
            else:
                return True
        else:
            return False

    def blockContent(self, contentId, contentVersion, blockExpiry=None):
        self._blockedContent[contentId] = (contentVersion, None if blockExpiry == None else QtCore.QDateTime.currentDateTimeUtc().addDays(blockExpiry))

class Download(Codable):
    def __init__(self):
        self.setDownloadSpeed(EngineConfig.RECOMMENDED_THREAD_LIMIT)

    def __setup__(self):
        self.reloadDownloadSpeed()

    def setDownloadSpeed(self, downloadSpeed):
        self._downloadSpeed = downloadSpeed
        self.reloadDownloadSpeed()

    def reloadDownloadSpeed(self):
        DownloadThreadPool.setMaxThreadCount(self._downloadSpeed)

    def getDownloadSpeed(self):
        return self._downloadSpeed


class Database:
    def __init__(self):
        self.version = Config.VERSION
        self.reset()
        App.aboutToQuit.connect(self.save)

    def load(self):
        self.reset()
        try:
            with open(Config.DB_FILE, "r", encoding="utf-8") as file:
                for key, value in Decoder.decode(Updaters.update(json.load(file))).items():
                    setattr(self, key, value)
        except Exception as e:
            App.logger.warning("Unable to load data.")
            App.logger.exception(e)
            self.reset()
            App.logger.info("Starting with default settings.")

    def save(self):
        try:
            OSUtils.createDirectory(Config.DB_ROOT)
            with open(Config.DB_FILE, "w", encoding="utf-8") as file:
                json.dump(Encoder.encode(self.__dict__), file, indent=3)
        except Exception as e:
            App.logger.error("Unable to save data.")
            App.logger.exception(e)

    def reset(self):
        self.setup = Setup()
        self.account = Account()
        self.general = General()
        self.templates = Templates()
        self.advanced = Advanced()
        self.localization = Localization()
        self.temp = Temp()
        self.download = Download()


DB = Database()
DB.load()