from .EncoderDecoder import Serializable, Encoder, Decoder
from .Updater import Updaters

from Core import App
from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Services.Utils.SystemUtils import SystemUtils
from Services.Logging.Logger import Logger
from Download.History import DownloadOptionHistory

from PyQt6 import QtCore

import json


class Setup(Serializable):
    def __init__(self):
        self._needSetup = True
        self._termsOfServiceAgreement = None

    def setupComplete(self) -> None:
        self._needSetup = False

    def needSetup(self) -> bool:
        return self._needSetup

    def agreeTermsOfService(self) -> None:
        self._termsOfServiceAgreement = QtCore.QDateTime.currentDateTimeUtc()

    def getTermsOfServiceAgreement(self) -> QtCore.QDateTime | None:
        return self._termsOfServiceAgreement


class Account(Serializable):
    def __init__(self):
        self._accountData = (None, None)

    def __setup__(self):
        App.Account.setData(*self._accountData)
        del self._accountData

    def __save__(self):
        self._accountData = App.Account.getData()
        return super().__save__()


class General(Serializable):
    def __init__(self):
        self._openProgressWindow = True
        self._notify = True
        self._useSystemTray = False
        self._bookmarks = []

    def setOpenProgressWindowEnabled(self, enabled: bool) -> None:
        self._openProgressWindow = enabled

    def setNotifyEnabled(self, enabled: bool) -> None:
        self._notify = enabled

    def setSystemTrayEnabled(self, enabled: bool) -> None:
        self._useSystemTray = enabled

    def setBookmarks(self, bookmarks: list[str]) -> None:
        self._bookmarks = bookmarks

    def isOpenProgressWindowEnabled(self) -> bool:
        return self._openProgressWindow

    def isNotifyEnabled(self) -> bool:
        return self._notify

    def isSystemTrayEnabled(self) -> bool:
        return self._useSystemTray

    def getBookmarks(self) -> list[str]:
        return self._bookmarks


class Templates(Serializable):
    def __init__(self):
        self._streamFilename = "[{type}] [{channel_name}] [{date}] {title} {resolution}"
        self._videoFilename = "[{type}] [{channel_name}] [{date}] {title} {resolution}"
        self._clipFilename = "[{type}] [{channel_name}] {title}"

    def setStreamFilename(self, filename: str) -> None:
        self._streamFilename = filename

    def setVideoFilename(self, filename: str) -> None:
        self._videoFilename = filename

    def setClipFilename(self, filename: str) -> None:
        self._clipFilename = filename

    def getStreamFilename(self) -> str:
        return self._streamFilename

    def getVideoFilename(self) -> str:
        return self._videoFilename

    def getClipFilename(self) -> str:
        return self._clipFilename


class Advanced(Serializable):
    def __init__(self):
        self._searchExternalContent = True

    def setSearchExternalContentEnabled(self, enabled: bool) -> None:
        self._searchExternalContent = enabled

    def isSearchExternalContentEnabled(self) -> bool:
        return self._searchExternalContent


class Localization(Serializable):
    def __init__(self):
        self._language = App.Translator.getDefaultLanguage()
        self._timezone = SystemUtils.getLocalTimezone()

    def __setup__(self):
        App.Translator.setLanguage(self._language)
        del self._language

    def __save__(self):
        self._language = App.Translator.getLanguage()
        return super().__save__()

    def setTimezone(self, timezone: bytes) -> None:
        self._timezone = SystemUtils.getTimezone(timezone)

    def getTimezone(self) -> QtCore.QTimeZone:
        return self._timezone

    def getTimezoneNameList(self) -> list[str]:
        return SystemUtils.getTimezoneNameList()


class Temp(Serializable):
    def __init__(self):
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
        App.DownloadHistory.setHistoryList(self._downloadHistory)
        del self._downloadHistory

    def __save__(self):
        self._downloadHistory = App.DownloadHistory.getHistoryList()
        return super().__save__()

    def getDownloadOptionHistory(self, historyType: DownloadOptionHistory.BaseOptionHistory) -> None:
        return self._downloadOptionHistory[historyType.getId()]

    def updateDownloadStats(self, fileSize: int) -> None:
        self._downloadStats["totalFiles"] += 1
        self._downloadStats["totalByteSize"] += fileSize

    def getDownloadStats(self) -> dict:
        return self._downloadStats

    def hasWindowGeometry(self, windowName: str) -> bool:
        return windowName in self._windowGeometry

    def setWindowGeometry(self, windowName: str, windowGeometry: bytes) -> None:
        self._windowGeometry[windowName] = windowGeometry

    def getWindowGeometry(self, windowName: str) -> bytes:
        return self._windowGeometry[windowName]

    def isContentBlocked(self, contentId: str | None, contentVersion: int | str) -> bool:
        if contentId in self._blockedContent:
            oldContentVersion, blockExpiration = self._blockedContent[contentId]
            if contentVersion != oldContentVersion or (blockExpiration != None and blockExpiration < QtCore.QDateTime.currentDateTimeUtc()):
                del self._blockedContent[contentId]
                return False
            else:
                return True
        else:
            return False

    def blockContent(self, contentId: str | None, contentVersion: int | str, blockExpiration: bool | int | None = None) -> None:
        self._blockedContent[contentId] = (contentVersion, None if blockExpiration == None else QtCore.QDateTime.currentDateTimeUtc().addDays(blockExpiration))


class Download(Serializable):
    def __init__(self):
        self._downloadSpeed = 20

    def __setup__(self):
        App.FileDownloadManager.setPoolSize(self._downloadSpeed)
        del self._downloadSpeed

    def __save__(self):
        self._downloadSpeed = App.FileDownloadManager.getPoolSize()
        return super().__save__()


class ScheduledDownloads(Serializable):
    def __init__(self):
        self._enabled = False
        self._scheduledDownloadPresets = []

    def __setup__(self):
        App.ScheduledDownloadManager.setEnabled(self._enabled)
        App.ScheduledDownloadManager.setPresets(self._scheduledDownloadPresets)
        del self._enabled
        del self._scheduledDownloadPresets

    def __save__(self):
        self._enabled = App.ScheduledDownloadManager.isEnabled()
        self._scheduledDownloadPresets = App.ScheduledDownloadManager.getPresets()
        return super().__save__()


class Preferences(QtCore.QObject):
    def __init__(self, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.logger = logger
        self.version = Config.APP_VERSION
        self._clearData()
        App.Instance.aboutToQuit.connect(self.save)

    def load(self) -> None:
        self._clearData()
        try:
            with open(Config.APPDATA_FILE, "r", encoding="utf-8") as file:
                for key, value in Decoder.decode(Updaters.update(json.load(file))).items():
                    setattr(self, key, value)
        except Exception as e:
            Updaters.CleanUnknownVersion()
            self.logger.warning("Unable to load data.")
            self.logger.exception(e)
            self.reset()
            self.logger.info("Starting with default settings.")

    def save(self) -> None:
        try:
            OSUtils.createDirectory(Config.APPDATA_PATH)
            with open(Config.APPDATA_FILE, "w", encoding="utf-8") as file:
                json.dump(Encoder.encode(self.getSaveData()), file, indent=3)
        except Exception as e:
            self.logger.error("Unable to save data.")
            self.logger.exception(e)

    def _clearData(self) -> None:
        self.setup = Setup()
        self.account = Account()
        self.general = General()
        self.templates = Templates()
        self.advanced = Advanced()
        self.localization = Localization()
        self.temp = Temp()
        self.download = Download()
        self.scheduledDownloads = ScheduledDownloads()

    def reset(self) -> None:
        self._clearData()
        self.setup.__setup__()
        self.account.__setup__()
        self.general.__setup__()
        self.templates.__setup__()
        self.advanced.__setup__()
        self.localization.__setup__()
        self.temp.__setup__()
        self.download.__setup__()
        self.scheduledDownloads.__setup__()

    def getSaveData(self) -> dict:
        exclude = ["logger"]
        return {key: value for key, value in self.__dict__.items() if key not in exclude}