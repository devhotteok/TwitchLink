import os
import pickle
import requests
import time
import pytz

from datetime import datetime

from TwitchLinkConfig import Config

from Services.TwitchLinkUtils import Utils
from Services.TwitchLinkTranslator import translator, T

from Auth.TwitchUserAuth import TwitchUser


class Setup:
    def __init__(self):
        self.version = Config.VERSION
        self.termsOfServiceAgreedTime = None

    def set(self, termsOfServiceAgreedTime):
        self.termsOfServiceAgreedTime = termsOfServiceAgreedTime

class Account:
    def __init__(self):
        self.user = TwitchUser()

class Settings:
    def __init__(self):
        self.enableMp4 = False
        self.autoClose = False
        self.engineType = "popcorn"
        self.bookmarks = []

    def set(self, enableMp4, autoClose, engineType, bookmarks):
        self.enableMp4 = enableMp4
        self.autoClose = autoClose
        self.engineType = engineType
        self.bookmarks = bookmarks

class Templates:
    def __init__(self):
        self.streamFilename = "[{type}] [{channel}] [{date}] {title}"
        self.videoFilename = "[{type}] [{channel}] [{date}] {title}"
        self.clipFilename = "[{type}] [{channel}] [{date}] {title}"

    def setFilename(self, streamFilename, videoFilename, clipFilename):
        self.streamFilename = streamFilename
        self.videoFilename = videoFilename
        self.clipFilename = clipFilename

class Localization:
    TIMEZONE = pytz.common_timezones

    def __init__(self):
        self.language = "en"
        self.setTimezone(self.TIMEZONE.index("US/Eastern"))

    def setLanguage(self, language):
        translator.setLanguage(language)
        self.language = language

    def setTimezone(self, timezoneNo):
        self.timezoneNo = timezoneNo
        self.timezone = datetime.now(pytz.timezone(self.TIMEZONE[timezoneNo])).utcoffset()

    def reloadTranslator(self):
        translator.setLanguage(self.language)

class Temp:
    def __init__(self):
        self.videoListWindowSize = "medium"
        self.tempDirectory = Config.TEMP_DIRECTORY
        self.fileSaveDirectory = Config.FILE_SAVE_DIRECTORY

    def setVideoListWindowSize(self, windowSize):
        self.videoListWindowSize = windowSize

    def setTempDirectory(self, tempDirectory):
        self.tempDirectory = tempDirectory

    def setFileSaveDirectory(self, fileSaveDirectory):
        self.fileSaveDirectory = fileSaveDirectory

class Engines:
    def __init__(self):
        self.popcorn = PopcornEngine()
        self.biscuit = BiscuitEngine()

class PopcornEngine:
    def __init__(self):
        self.fastDownload = True
        self.updateTracking = False

    def set(self, fastDownload, updateTracking):
        self.fastDownload = fastDownload
        self.updateTracking = updateTracking

class BiscuitEngine:
    def __init__(self):
        pass

    def set(self):
        pass

class DataBase:
    def __init__(self):
        self.loadDB()
        self.forcedClose = False
        self.downloading = False

    def checkStatus(self):
        try:
            response = requests.get(Config.SERVER_URL + "/status.json")
        except:
            self.programStatus = "Server Error"
            return
        if response.status_code == 200:
            data = response.json()
            self.programStatus = ""
            try:
                status = data["status"]
                self.statusMessage = status["message"].get(translator.getLanguage())
                self.serverNotice = data["notice"].get(translator.getLanguage())
                if not status["running"]:
                    self.programStatus = "Unavailable"
                    return
                version = data["version"]
                self.updateNote = version["updateNote"].get(translator.getLanguage())
                self.updateUrl = version["updateUrl"]
                if version["versionNo"] != Config.VERSION:
                    if version["updateRequired"]:
                        self.programStatus = "Update Required"
                        return
                    else:
                        self.programStatus = "Update Found"
                if self.getConfigData():
                    if self.programStatus != "Update Found":
                        self.programStatus = "Available"
                else:
                    self.programStatus = "Server Error"
            except:
                self.programStatus = "Update Required"
                self.updateNote = None
                self.updateUrl = Config.HOMEPAGE_URL
        else:
            self.programStatus = "Server Error"

    def getConfigData(self):
        try:
            response = requests.get(Config.SERVER_URL + "/config.json")
        except:
            return False
        if response.status_code == 200:
            data = response.json()
            Config.AD_SERVER = data["ads"][self.localization.language]["AD_SERVER"]
            Config.SHOW_ADS = data["ads"][self.localization.language]["SHOW_ADS"]
            return True
        else:
            return False

    def setUi(self, ui):
        self.ui = ui

    def setApp(self, app):
        self.app = app

    def setMainWindow(self, window):
        self.mainWindow = window

    def setApi(self, api):
        self.api = api

    def forceClose(self):
        self.forcedClose = True
        self.app.closeAllWindows()

    def restartApp(self):
        self.app.exit(-1)

    def saveDB(self):
        db = {
            "setup": self.setup,
            "account": self.account,
            "settings": self.settings,
            "templates": self.templates,
            "localization": self.localization,
            "temp": self.temp,
            "engines": self.engines
        }
        try:
            Utils.createDirectory(Config.DB_ROOT)
            with open(Config.DB_FILE, "wb") as file:
                pickle.dump(db, file)
        except:
            Utils.info("system-error", "#A system error has occurred.\n\nPossible Causes\n\n* Invalid file name or path\n* Out of storage capacity\nIf the error persists, try Run as administrator.")

    def openDB(self):
        try:
            with open(Config.DB_FILE, "rb") as file:
                return pickle.load(file)
        except:
            return None

    def loadDB(self):
        db = self.openDB()
        try:
            self.setup = db["setup"]
            self.account = db["account"]
            self.settings = db["settings"]
            self.templates = db["templates"]
            self.localization = db["localization"]
            self.temp = db["temp"]
            self.engines = db["engines"]
            if self.setup.version != Config.VERSION:
                if self.setup.version in Config.DB_COMPATIBLE_VERSIONS:
                    self.setup.version = Config.VERSION
                    self.saveDB()
                else:
                    self.resetDB()
        except:
            self.resetDB()
        self.localization.reloadTranslator()

    def resetDB(self):
        self.setup = Setup()
        self.account = Account()
        self.settings = Settings()
        self.templates = Templates()
        self.localization = Localization()
        self.temp = Temp()
        self.engines = Engines()
        self.saveDB()

    def resetSettings(self):
        self.resetDB()
        self.restartApp()

    def saveLogs(self, logs):
        try:
            if not os.path.exists(Config.LOG_FILE):
                with open(Config.LOG_FILE, "w", encoding="utf-8") as file:
                    file.write("{} Download Logs".format(Config.PROJECT_NAME))
            with open(Config.LOG_FILE, "a", encoding="utf-8") as file:
                file.write("\n\n" + logs)
        except:
            Utils.info("system-error", "#A system error has occurred.\n\nPossible Causes\n\n* Invalid file name or path\n* Out of storage capacity\nIf the error persists, try Run as administrator.")

    def agreeTermsOfService(self):
        self.setup.set(datetime.now())
        self.saveDB()

    def setGeneralSettings(self, enableMp4, autoClose, engineType, bookmarks):
        self.settings.set(enableMp4, autoClose, engineType, bookmarks)
        self.saveDB()

    def setFilenameSettings(self, streamFilename, videoFilename, clipFilename):
        self.templates.setFilename(streamFilename, videoFilename, clipFilename)
        self.saveDB()

    def setLanguage(self, languageNo):
        language = list(translator.LANGUAGES.keys())[languageNo]
        self.localization.setLanguage(language)
        self.saveDB()
        Utils.info("restart", "#Restart due to language change.")
        self.restartApp()

    def setTimezone(self, timezoneNo):
        self.localization.setTimezone(timezoneNo)
        self.saveDB()
        Utils.info("restart", "#Restart due to time zone change.")
        self.restartApp()

    def setPopcornEngineSettings(self, fastDownload, updateTracking):
        self.engines.popcorn.set(fastDownload, updateTracking)
        self.saveDB()

    def setBiscuitEngineSettings(self):
        self.engines.biscuit.set()
        self.saveDB()

    def setDownloadingState(self, state):
        self.downloading = state

    def setupDownload(self, dataModel, accessToken):
        try:
            Utils.createDirectory(self.temp.fileSaveDirectory)
        except:
            pass
        if accessToken.dataType == "stream":
            stream = dataModel
            streamData = accessToken
            kwargs = {
                "type": T("stream"),
                "id": stream.id,
                "title": stream.title,
                "game": stream.game.displayName,
                "channel": stream.broadcaster.displayName,
                "started_at": stream.createdAt.toUTC(self.localization.timezone),
                "date": stream.createdAt.date(self.localization.timezone),
                "time": stream.createdAt.time(self.localization.timezone)
            }
            logs = "[Stream] [{channel}] [{started_at}] {title}".format(**kwargs)
            fileName = Utils.safeFormat(self.templates.streamFilename, **kwargs)
            fileName = self.getSafeFileName(fileName) + ".ts"
            self.fileDownload = {"downloadType": "stream", "stream": stream, "streamData": streamData, "resolution": streamData.getResolutions()[0], "fileName": fileName, "saveDirectory": self.temp.fileSaveDirectory}
        elif accessToken.dataType == "video":
            video = dataModel
            videoData = accessToken
            kwargs = {
                "type": T("video"),
                "id": video.id,
                "title": video.title,
                "game": video.game.displayName,
                "channel": video.owner.displayName,
                "duration": video.lengthSeconds,
                "published_at": video.publishedAt.toUTC(self.localization.timezone),
                "date": video.publishedAt.date(self.localization.timezone),
                "time": video.publishedAt.time(self.localization.timezone),
                "views": video.viewCount
            }
            logs = "[Video] [{channel}] [{published_at}] {title}".format(**kwargs)
            fileName = Utils.safeFormat(self.templates.videoFilename, **kwargs)
            fileName = self.getSafeFileName(fileName) + ".ts"
            self.fileDownload = {"downloadType": "video", "video": video, "videoData": videoData, "resolution": videoData.getResolutions()[0], "range": [None, None], "fileName": fileName, "saveDirectory": self.temp.fileSaveDirectory}
        else:
            clip = dataModel
            clipData = accessToken
            kwargs = {
                "type": T("clip"),
                "id": clip.id,
                "title": clip.title,
                "game": clip.game.displayName,
                "slug": clip.slug,
                "channel": clip.broadcaster.displayName,
                "creator": clip.curator.displayName,
                "duration": clip.durationSeconds,
                "created_at": clip.createdAt.toUTC(self.localization.timezone),
                "date": clip.createdAt.date(self.localization.timezone),
                "time": clip.createdAt.time(self.localization.timezone),
                "views": clip.viewCount
            }
            logs = "[Clip] [{channel}] [{created_at}] {title}".format(**kwargs)
            fileName = Utils.safeFormat(self.templates.clipFilename, **kwargs)
            fileName = self.getSafeFileName(fileName) + ".mp4"
            self.fileDownload = {"downloadType": "clip", "clip": clip, "clipData": clipData, "resolution": clipData.getResolutions()[0], "fileName": fileName, "saveDirectory": self.temp.fileSaveDirectory}
        self.saveLogs(logs + "\n" + accessToken.resolution(self.fileDownload["resolution"]).url.split("?")[0])

    def getSafeFileName(self, name):
        characters = {
            "\\": "￦",
            "/": "／",
            ":": "：",
            "*": "＊",
            "?": "？",
            "\"": "＂",
            "<": "＜",
            ">": "＞",
            "|": "｜",
            "\n": "",
            "\r": "",
        }
        for key, value in characters.items():
            name = name.replace(key, value)
        return name.strip()

    def setDownloadResolution(self, resolution):
        accessToken = self.fileDownload[self.fileDownload["downloadType"] + "Data"]
        self.fileDownload["resolution"] = accessToken.getResolutions()[resolution]

    def setCropRange(self, start, end):
        self.fileDownload["range"] = [start, end]

    def cancelDownload(self):
        self.fileDownload = None

    def checkDownload(self):
        if self.fileDownload == None:
            return False
        else:
            return True

    def setVideoListWindowSize(self, windowSize):
        self.temp.setVideoListWindowSize(windowSize)
        self.saveDB()

    def setTempDirectory(self, directory):
        self.temp.setTempDirectory(directory)
        self.saveDB()

    def setFileSaveDirectory(self, directory):
        self.temp.setFileSaveDirectory("/".join(directory.split("/")[:-1]))
        self.fileDownload["fileName"] = directory.split("/")[-1]
        self.fileDownload["saveDirectory"] = self.temp.fileSaveDirectory
        self.saveDB()

    def downloadClip(self, progressSignal):
        url = self.fileDownload["clipData"].resolution(self.fileDownload["resolution"]).url
        file = self.fileDownload["saveDirectory"] + "/" + self.fileDownload["fileName"]
        downloader = Utils.FileDownloader(url, file)
        while True:
            progressSignal.emit(T("#Downloading..."), downloader.progress)
            if downloader.done:
                break
            time.sleep(0.1)
        self.fileDownload = None
        if downloader.failed:
            progressSignal.emit(T("download-failed"), downloader.progress)
            if downloader.reason == "NetworkError":
                Utils.info("download-failed", "#A network error has occurred.")
            else:
                Utils.info("system-error", "#A system error has occurred.\n\nPossible Causes\n\n* Invalid file name or path\n* Out of storage capacity\nIf the error persists, try Run as administrator.")
        else:
            progressSignal.emit(T("download-complete"), downloader.progress)
            Utils.info("download-complete", "#Download completed.")