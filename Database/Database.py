from .EncoderDecoder import Codable, Encoder, Decoder
from .Updater import Updaters

from Core.App import App
from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Services.Utils.SystemUtils import SystemUtils

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
        from Services.Account.TwitchAccount import TwitchAccount
        self._account = TwitchAccount()

    def login(self, username, token, expiry):
        self._account.login(username, token, expiry)

    def logout(self):
        self._account.logout()

    def updateAccount(self):
        self._account.updateAccount()

    def isUserLoggedIn(self):
        return self._account.isConnected()

    @property
    def user(self):
        return self._account.data

    def checkAuthToken(self):
        self._account.checkToken()

    def getAuthToken(self):
        self.checkAuthToken()
        return self._account.token

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
        self._caching = False

    def __setup__(self):
        from Services.Image.Loader import ImageLoader
        ImageLoader.setCachingEnabled(self._caching)
        del self._caching

    def __save__(self):
        from Services.Image.Loader import ImageLoader
        self._caching = ImageLoader.isCachingEnabled()
        return super().__save__()

    def setSearchExternalContentEnabled(self, enabled):
        self._searchExternalContent = enabled

    def isSearchExternalContentEnabled(self):
        return self._searchExternalContent

class Localization(Codable):
    def __init__(self):
        from Services.Translator.Translator import Translator
        self._language = Translator.getDefaultLanguage()
        self._timezone = SystemUtils.getLocalTimezone()

    def __setup__(self):
        from Services.Translator.Translator import Translator
        Translator.setLanguage(self._language)
        del self._language

    def __save__(self):
        from Services.Translator.Translator import Translator
        self._language = Translator.getLanguage()
        return super().__save__()

    def setTimezone(self, timezone):
        self._timezone = SystemUtils.getTimezone(timezone)

    def getTimezone(self):
        return self._timezone

    def getTimezoneNameList(self):
        return SystemUtils.getTimezoneNameList()

class Temp(Codable):
    def __init__(self):
        from Download import DownloadOptionHistory
        self._downloadHistory = []
        self._downloadOptionHistory = {
            history.getId(): history() for history in [
                DownloadOptionHistory.StreamHistory,
                DownloadOptionHistory.VideoHistory,
                DownloadOptionHistory.ClipHistory,
                DownloadOptionHistory.ThumbnailHistory,
                DownloadOptionHistory.ScheduledDownloadHistory
            ]
        }
        self._downloadStats = {
            "totalFiles": 0,
            "totalByteSize": 0
        }
        self._windowGeometry = {}
        self._blockedContent = {}

    def __setup__(self):
        from Download.DownloadHistoryManager import DownloadHistoryManager
        DownloadHistoryManager.setHistoryList(self._downloadHistory)
        del self._downloadHistory

    def __save__(self):
        from Download.DownloadHistoryManager import DownloadHistoryManager
        self._downloadHistory = DownloadHistoryManager.getHistoryList()
        return super().__save__()

    def getDownloadOptionHistory(self, historyType):
        return self._downloadOptionHistory[historyType.getId()]

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
        from Download.Downloader.Engine.Config import Config as DownloadEngineConfig
        self._downloadSpeed = DownloadEngineConfig.RECOMMENDED_THREAD_LIMIT

    def __setup__(self):
        from Download.Downloader.Engine.ThreadPool import DownloadThreadPool
        DownloadThreadPool.setMaxThreadCount(self._downloadSpeed)
        del self._downloadSpeed

    def __save__(self):
        from Download.Downloader.Engine.ThreadPool import DownloadThreadPool
        self._downloadSpeed = DownloadThreadPool.maxThreadCount()
        return super().__save__()

class ScheduledDownloads(Codable):
    def __init__(self):
        self._enabled = True
        self._scheduledDownloadPresets = []

    def __setup__(self):
        from Download.ScheduledDownloadManager import ScheduledDownloadManager
        ScheduledDownloadManager.setEnabled(self._enabled)
        ScheduledDownloadManager.setPresets(self._scheduledDownloadPresets)
        del self._enabled
        del self._scheduledDownloadPresets

    def __save__(self):
        from Download.ScheduledDownloadManager import ScheduledDownloadManager
        self._enabled = ScheduledDownloadManager.isEnabled()
        self._scheduledDownloadPresets = ScheduledDownloadManager.getPresets()
        return super().__save__()


class Database:
    def __init__(self):
        self.version = Config.APP_VERSION
        self._resetData()
        App.aboutToQuit.connect(self.save)

    def load(self):
        self._resetData()
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

    def _resetData(self):
        self.setup = Setup()
        self.account = Account()
        self.general = General()
        self.templates = Templates()
        self.advanced = Advanced()
        self.localization = Localization()
        self.temp = Temp()
        self.download = Download()
        self.scheduledDownloads = ScheduledDownloads()

    def reset(self):
        self._resetData()
        self.setup.__setup__()
        self.account.__setup__()
        self.general.__setup__()
        self.templates.__setup__()
        self.advanced.__setup__()
        self.localization.__setup__()
        self.temp.__setup__()
        self.download.__setup__()
        self.scheduledDownloads.__setup__()


DB = Database()
DB.load()