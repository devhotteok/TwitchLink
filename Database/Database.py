from .EncoderDecoder import Encoder, Decoder
from .Loader import DataLoader

from Core.App import App
from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Services.Utils.SystemUtils import SystemUtils
from Services.Image.Loader import ImageLoader
from Services.Image.Config import Config as ImageConfig
from Services.Account.Auth import TwitchAccount
from Services.Twitch.Playback.TwitchPlaybackAccessTokens import TwitchPlaybackAccessTokenTypes
from Services.Translator.Translator import Translator
from Download import DownloadHistory
from Download.Downloader.Engine.ThreadPool import ThreadPool as DownloadThreadPool
from Download.Downloader.Engine.Config import Config as EngineConfig

import json

from datetime import datetime, timedelta


class Setup:
    def __init__(self):
        self._needSetup = True
        self._termsOfServiceAgreement = None

    def setupComplete(self):
        self._needSetup = False

    def needSetup(self):
        return self._needSetup

    def agreeTermsOfService(self):
        self._termsOfServiceAgreement = datetime.now()

    def getTermsOfServiceAgreement(self):
        return self._termsOfServiceAgreement

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
        return self._user.isConnected()

    def getAccountData(self):
        return self._user.data

    def checkAuthToken(self):
        self._user.checkToken()

    def getAuthToken(self):
        return self._user.token

class General:
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

class Advanced:
    def __init__(self):
        self._externalContentUrl = True
        self.setCachingEnabled(False)

    def setExternalContentUrlEnabled(self, enabled):
        self._externalContentUrl = enabled

    def setCachingEnabled(self, enabled):
        self._caching = enabled
        self.reloadCaching()

    def reloadCaching(self):
        ImageLoader.setCachingEnabled(self._caching)

    def isExternalContentUrlEnabled(self):
        return self._externalContentUrl

    def isCachingEnabled(self):
        return self._caching

class Localization:
    def __init__(self):
        self.setLanguage(Translator.getDefaultLanguage())
        self._timezone = SystemUtils.getLocalTimezone(preferred=Translator.getLanguageData()[Translator.getDefaultLanguage()]["preferredTimezone"])

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

    def getTimezoneList(self):
        return SystemUtils.getTimezoneList()

class Temp:
    def __init__(self):
        self._downloadHistory = {
            TwitchPlaybackAccessTokenTypes.STREAM: DownloadHistory.StreamHistory(),
            TwitchPlaybackAccessTokenTypes.VIDEO: DownloadHistory.VideoHistory(),
            TwitchPlaybackAccessTokenTypes.CLIP: DownloadHistory.ClipHistory(),
            ImageConfig.DATA_TYPE: DownloadHistory.ThumbnailHistory()
        }
        self._windowGeometry = {}
        self._blockedContent = {}

    def getDownloadHistory(self, contentType):
        return self._downloadHistory[contentType]

    def hasWindowGeometry(self, windowName):
        return windowName in self._windowGeometry

    def setWindowGeometry(self, windowName, windowGeometry):
        self._windowGeometry[windowName] = windowGeometry

    def getWindowGeometry(self, windowName):
        return self._windowGeometry[windowName]

    def isContentBlocked(self, contentId, contentVersion):
        if contentId in self._blockedContent:
            oldContentVersion, blockExpiry = self._blockedContent[contentId]
            if contentVersion != oldContentVersion or (blockExpiry != None and blockExpiry < datetime.now()):
                del self._blockedContent[contentId]
                return False
            else:
                return True
        else:
            return False

    def blockContent(self, contentId, contentVersion, blockExpiry=None):
        self._blockedContent[contentId] = (contentVersion, None if blockExpiry == None else datetime.now() + timedelta(days=blockExpiry))

class Download:
    def __init__(self):
        self.setDownloadSpeed(EngineConfig.RECOMMENDED_THREAD_LIMIT)

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
        self.load()
        App.aboutToQuit.connect(self.save)

    def load(self):
        self.reset()
        try:
            with open(Config.DB_FILE, "r", encoding="utf-8") as file:
                DataLoader.load(self, Decoder.decode(json.load(file)))
        except Exception as e:
            App.logger.critical("Unable to load data.")
            App.logger.exception(e)
            self.reset()
            App.logger.info("Starting with default settings.")
        self.advanced.reloadCaching()
        self.localization.reloadTranslator()
        self.download.reloadDownloadSpeed()

    def save(self):
        try:
            OSUtils.createDirectory(Config.DB_ROOT)
            with open(Config.DB_FILE, "w", encoding="utf-8") as file:
                json.dump(Encoder.encode(self), file, indent=3)
        except Exception as e:
            App.logger.critical("Unable to save data.")
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