import os
import threading
import time
import gc

from PyQt5.QtCore import Qt, QRegExp, QUrl, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap, QDesktopServices
from PyQt5.QtWidgets import QMainWindow, QWidget, QDialog, QDialogButtonBox, QLabel, QTextBrowser

from TwitchLinkConfig import Config

from Services.Twitch import TwitchGqlModels
from Services.TwitchLinkUiLoader import uiLoader as UiFiles
from Services.Twitch.TwitchPlaybackAccessTokens import *
from Services.TwitchLinkUtils import Utils
from Services.TwitchLinkAdManager import AdManager
from Services.TwitchLinkTranslator import translator, T

from Auth.TwitchUserAuth import BrowserNotFoundError, BrowserNotLoadableError

from Engines.TwitchLinkPopcornEngine import TwitchDownloader as TwitchDownloaderPopcornEngine
from Engines.TwitchLinkBiscuitEngine import TwitchDownloader as TwitchDownloaderBiscuitEngine


class Ui:
    def __init__(self, db):
        self.db = db

    def Loading(self):
        return self.setup(Loading(self.db), forceAllLabelFonts=True)

    def Settings(self):
        return self.setup(Settings(self.db), forceAllLabelFonts=True)

    def Login(self):
        return self.setup(Login(self.db), forceAllLabelFonts=True)

    def About(self):
        return self.setup(About(self.db))

    def TermsOfService(self):
        return self.setup(TermsOfService(self.db))

    def MainMenu(self):
        return self.setup(MainMenu(self.db))

    def Search(self, mode):
        return self.setup(Search(self.db, mode))

    def VideoFrame(self, data):
        return self.setup(VideoFrame(self.db, data))

    def VideoBox(self, window, video):
        return self.setup(VideoBox(self.db, window, video))

    def VideoList(self, mode, data):
        return self.setup(VideoList(self.db, mode, data), forceSize=False, forceAllLabelFonts=True)

    def DownloadMenu(self, video, vod):
        return self.setup(DownloadMenu(self.db, video, vod), forceAllLabelFonts=True)

    def Download(self):
        return self.setup(Download(self.db), forceAllLabelFonts=True)

    def setup(self, ui, forceSize=True, forceAllLabelFonts=False):
        if isinstance(ui, QDialog):
            ui.setWindowIcon(QIcon(Config.ICON_IMAGE))
        title = ui.windowTitle()
        if title == "":
            ui.setWindowTitle(T("#PROGRAM_NAME"))
        else:
            ui.setWindowTitle("{} - {}".format(T("#PROGRAM_NAME"), T(title)))
        ui.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        ui = self.setAds(ui)
        if forceSize:
            if isinstance(ui, QDialog):
                if Config.SHOW_ADS:
                    ui.setFixedSize(ui.size())
                else:
                    ui.setFixedSize(ui.width() - ui.adSize[0], ui.height() - ui.adSize[1])
        ui.setFont(translator.getFont())
        for widget in ui.findChildren(QTextBrowser):
            widget.setFont(translator.getDocFont(widget.font()))
        if forceAllLabelFonts:
            for widget in ui.findChildren(QLabel):
                widget.setFont(translator.getFont(widget.font()))
        return ui

    def setAds(self, ui):
        for ad in ui.findChildren(QLabel, QRegExp("^ad_\d+$")):
            if Config.SHOW_ADS:
                ad.parent().layout().addWidget(AdManager(ad.width(), ad.height()))
                ad.setParent(None)
            else:
                ad.parent().setParent(None)
        return ui

class Loading(QMainWindow, UiFiles.loading):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setupUi(self)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon(Config.ICON_IMAGE))
        self.programLogo.setContentsMargins(10, 10, 10, 10)
        self.programLogo.setPixmap(Utils.Image(Config.LOGO_IMAGE))

class Settings(QDialog, UiFiles.settings):
    adSize = [0, 0]

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setupUi(self)
        self.enableMp4.setChecked(self.db.settings.enableMp4)
        self.autoClose.setChecked(self.db.settings.autoClose)
        self.popcornEngine.setChecked(self.db.settings.engineType == "popcorn")
        self.biscuitEngine.setChecked(self.db.settings.engineType == "biscuit")
        self.downloadEngineInfo.clicked.connect(self.showDownloadEngineInfo)
        self.streamFilename.setText(self.db.templates.streamFilename)
        self.videoFilename.setText(self.db.templates.videoFilename)
        self.clipFilename.setText(self.db.templates.clipFilename)
        self.streamTemplateInfo.clicked.connect(self.showStreamTemplateInfo)
        self.videoTemplateInfo.clicked.connect(self.showVideoTemplateInfo)
        self.clipTemplateInfo.clicked.connect(self.showClipTemplateInfo)
        self.bookmarkList.addItems(self.db.settings.bookmarks)
        self.newBookmark.returnPressed.connect(self.addBookmark)
        self.addBookmarkButton.clicked.connect(self.addBookmark)
        self.insertBookmarkButton.clicked.connect(self.insertBookmark)
        self.removeBookmarkButton.clicked.connect(self.removeBookmark)
        self.currentTempDirectory.setText(self.db.temp.tempDirectory)
        self.currentTempDirectory.setCursorPosition(0)
        self.tempDirectoryInfo.clicked.connect(self.showTempDirectoryInfo)
        self.searchTempDirectory.clicked.connect(self.askTempDirectory)
        self.language.addItems(list(translator.LANGUAGES.values()))
        self.language.setCurrentIndex(list(translator.LANGUAGES.keys()).index(self.db.localization.language))
        self.language.currentIndexChanged.connect(self.setLanguage)
        self.timezone.addItems(self.db.localization.TIMEZONE)
        self.timezone.setCurrentIndex(self.db.localization.timezoneNo)
        self.timezone.currentIndexChanged.connect(self.setTimezone)
        self.popcornEngineInfo.setHtml(Utils.getDocs(self.db.localization.language, "PopcornEngine"))
        self.biscuitEngineInfo.setHtml(Utils.getDocs(self.db.localization.language, "BiscuitEngine"))
        self.popcornFastDownload.setChecked(self.db.engines.popcorn.fastDownload)
        self.popcornUpdateTracking.setChecked(self.db.engines.popcorn.updateTracking)
        self.popcornNormal.setChecked(not self.db.engines.popcorn.updateTracking)
        if self.db.downloading:
            self.engineArea.setEnabled(False)
            self.languageArea.setEnabled(False)
            self.timezoneArea.setEnabled(False)
            self.popcornSettingsArea.setEnabled(False)
            self.popcornDownloadModeArea.setEnabled(False)
            self.buttonBox.button(QDialogButtonBox.Reset).setEnabled(False)
        else:
            self.restrictedLabel.hide()
        self.buttonBox.accepted.connect(self.saveSettings)
        self.buttonBox.button(QDialogButtonBox.Reset).clicked.connect(self.resetSettings)

    def keyPressEvent(self, event):
        if ((not event.modifiers() and event.key() == Qt.Key_Return) or (event.modifiers() == Qt.KeypadModifier and event.key() == Qt.Key_Enter)):
            event.accept()
        else:
            super().keyPressEvent(event)

    def showDownloadEngineInfo(self):
        info = "#Select your download engine.\nThese settings apply only to video downloads.\nThe live download is automatically fixed with [Biscuit Engine].\nThe clips are downloaded without an engine."
        Utils.info("notification", info)

    def showStreamTemplateInfo(self):
        info = "#{type} : File Type (Stream)\n{id} : Stream ID (XXXXXXXXXX)\n{title} : Title\n{game} : Category\n{channel} : Channel\n{started_at} : Started At (XXXX-XX-XX XX:XX:XX)\n{date} : Started Date (XXXX-XX-XX)\n{time} : Started Time (XX:XX:XX)"
        Utils.info("#Stream Filename Template Variables", info, noFormat=True)

    def showVideoTemplateInfo(self):
        info = "#{type} : File Type (Video)\n{id} : Video ID (XXXXXXXXXX)\n{title} : Title\n{game} : Category\n{channel} : Channel\n{duration} : Duration\n{published_at} : Published At (XXXX-XX-XX XX:XX:XX)\n{date} : Published Date (XXXX-XX-XX)\n{time} : Published Time (XX:XX:XX)\n{views} : Views"
        Utils.info("#Video Filename Template Variables", info, noFormat=True)

    def showClipTemplateInfo(self):
        info = "#{type} : File Type (Clip)\n{id} : Clip ID (XXXXXXXXXX)\n{title} : Title\n{game} : Category\n{slug} : Slug (HappySlugExampleHelloTwitch)\n{channel} : Channel\n{creator} : Creator\n{duration} : Duration\n{created_at} : Created At (XXXX-XX-XX XX:XX:XX)\n{date} : Created Date (XXXX-XX-XX)\n{time} : Created Time (XX:XX:XX)\n{views} : Views"
        Utils.info("#Clip Filename Template Variables", info, noFormat=True)

    def addBookmark(self):
        bookmark = self.newBookmark.text().strip().lower()
        if bookmark == "":
            return
        if len(self.bookmarkList.findItems(bookmark, Qt.MatchFixedString)) == 0:
            self.bookmarkList.addItem(bookmark)
            self.newBookmark.clear()
        else:
            Utils.info("warning", "#Bookmark already exists.")

    def insertBookmark(self):
        bookmark = self.newBookmark.text().strip().lower()
        if bookmark == "":
            return
        if len(self.bookmarkList.findItems(bookmark, Qt.MatchFixedString)) == 0:
            self.bookmarkList.insertItem(self.bookmarkList.currentRow(), bookmark)
            self.newBookmark.clear()
        else:
            Utils.info("warning", "#Bookmark already exists.")

    def removeBookmark(self):
        self.bookmarkList.takeItem(self.bookmarkList.currentRow())

    def showTempDirectoryInfo(self):
        Utils.info("notification", "#A place to store various temporary data.\nAllocate it to a disk with a lot of free space.\n\nIt is mainly used for temporary storage of video data in [Popcorn Engine].\n[Popcorn Engine] processes download and encoding separately, which requires additional free space as much as the size of the video to be downloaded.\nWhen the download is complete or canceled, all temporary data will be deleted.\n[Biscuit Engine] does not require this free space.")

    def askTempDirectory(self):
        newDirectory = Utils.askFileDirectory(self, self.db.temp.tempDirectory)
        if newDirectory != "":
            self.db.setTempDirectory(newDirectory)
            self.currentTempDirectory.setText(newDirectory)
            self.currentTempDirectory.setCursorPosition(0)

    def setLanguage(self, index):
        self.saveSettings()
        self.db.setLanguage(index)

    def setTimezone(self, index):
        self.saveSettings()
        self.db.setTimezone(index)

    def saveSettings(self):
        enableMp4 = self.enableMp4.isChecked()
        autoClose = self.autoClose.isChecked()
        if self.popcornEngine.isChecked():
            engineType = "popcorn"
        else:
            engineType = "biscuit"
        streamFilename = self.streamFilename.text()
        videoFilename = self.videoFilename.text()
        clipFilename = self.clipFilename.text()
        bookmarks = []
        for index in range(self.bookmarkList.count()):
            bookmarks.append(self.bookmarkList.item(index).text())
        popcornFastDownload = self.popcornFastDownload.isChecked()
        popcornUpdateTracking = self.popcornUpdateTracking.isChecked()
        self.db.setGeneralSettings(enableMp4, autoClose, engineType, bookmarks)
        self.db.setFilenameSettings(streamFilename, videoFilename, clipFilename)
        self.db.setPopcornEngineSettings(popcornFastDownload, popcornUpdateTracking)
        self.db.setBiscuitEngineSettings()

    def resetSettings(self):
        if Utils.ask("reset-settings", "#This will reset all settings, including logs.\nWould you like to continue?"):
            self.db.resetSettings()

class Login(QDialog, UiFiles.login):
    adSize = [0, 0]

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        try:
            self.db.account.user.reloadUser(self.db.api)
        except:
            pass
        if self.db.account.user.connected:
            self.accountMenu.setCurrentIndex(1)
            self.profile_image.setPixmap(Utils.Image(self.db.account.user.data.profileImageURL, Config.PROFILE_IMAGE))
            self.account.setText(self.db.account.user.data.displayName)
            self.logoutButton.clicked.connect(self.tryLogout)
        else:
            self.accountMenu.setCurrentIndex(0)
            self.loginInfo.hide()
            self.loginButton.clicked.connect(self.tryLogin)
            self.loginButton.setAutoDefault(True)

    def tryLogin(self):
        self.setEnabled(False)
        self.loginInfo.show()
        self.loginButton.setText(T("#Logging in..."))
        self.loginThread = LoginThread(self.db)
        self.loginThread.loginResult.connect(self.loginResult)
        self.loginThread.start()

    def loginResult(self, result):
        self.setEnabled(True)
        self.loginInfo.hide()
        self.loginButton.setText(T("login"))
        if result == "Succeed":
            Utils.info("login", "#Login complete.")
            self.close()
        elif result == "BrowserNotFound":
            Utils.info("error", "#Chrome browser or Edge browser is required to proceed.")
        elif result == "BrowserNotLoadable":
            Utils.info("error", "#Unable to load Chrome browser or Edge browser.\nIf the error persists, try Run as administrator.")
        else:
            Utils.info("error", "#Login failed.")

    def tryLogout(self):
        if Utils.ask("logout", "#Are you sure you want to log out?"):
            self.db.account.user.logout()
            self.db.saveDB()
            Utils.info("logout", "#Logout complete.")
            self.close()

    def closeEvent(self, event):
        if not self.isEnabled():
            event.ignore()

class LoginThread(QThread):
    loginResult = pyqtSignal(str)

    def __init__(self, db):
        super().__init__()
        self.db = db

    def run(self):
        try:
            self.db.account.user.login(self.db.api, Config.APPDATA_PATH + "/webdrivers")
            self.db.saveDB()
            self.loginResult.emit("Succeed")
        except BrowserNotFoundError:
            self.loginResult.emit("BrowserNotFound")
        except BrowserNotLoadableError:
            self.loginResult.emit("BrowserNotLoadable")
        except:
            self.loginResult.emit("Error")

class About(QDialog, UiFiles.about):
    adSize = [0, 0]

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setupUi(self)
        self.versionLabel.setText("v {}".format(Config.VERSION))
        self.homepageButton.clicked.connect(self.openHomepage)
        self.donateButton.clicked.connect(self.openDonate)

    def openHomepage(self):
        QDesktopServices.openUrl(QUrl(Config.HOMEPAGE_URL + "?lang=" + self.db.localization.language))

    def openDonate(self):
        QDesktopServices.openUrl(QUrl(Config.HOMEPAGE_URL + "/donate?lang=" + self.db.localization.language))

class TermsOfService(QDialog, UiFiles.termsOfService):
    adSize = [0, 0]

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setupUi(self)
        self.selectLanguage.clicked.connect(self.db.mainWindow.openSettings)
        self.textBrowser.setHtml(Utils.getDocs(self.db.localization.language, "TermsOfService"))
        if self.db.setup.termsOfServiceAgreedTime == None:
            self.setWindowFlag(Qt.WindowCloseButtonHint, False)
            self.agreed.hide()
            self.agree.stateChanged.connect(self.checkAgree)
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
            self.buttonBox.accepted.connect(self.db.agreeTermsOfService)
            self.buttonBox.rejected.connect(self.db.forceClose)
        else:
            self.agree.hide()
            self.agreed.setText(T("#Agreed at {time}", time=str(self.db.setup.termsOfServiceAgreedTime).split(".")[0]))
            self.buttonBox.setStandardButtons(QDialogButtonBox.Ok)

    def checkAgree(self):
        if self.agree.isChecked():
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)

class MainMenu(QWidget, UiFiles.mainMenu):
    adSize = [100, 50]

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setupUi(self)
        self.programLogo.setContentsMargins(10, 10, 10, 10)
        self.programLogo.setPixmap(Utils.Image(Config.LOGO_IMAGE))
        self.channel_id.clicked.connect(lambda: self.db.mainWindow.startSearch("channel_id"))
        self.video_id.clicked.connect(lambda: self.db.mainWindow.startSearch("video_id"))
        self.video_url.clicked.connect(lambda: self.db.mainWindow.startSearch("video_url"))

class Search(QDialog, UiFiles.search):
    adSize = [0, 0]

    def __init__(self, db, mode):
        super().__init__()
        self.db = db
        self.setupUi(self)
        self.setup(mode)

    def setup(self, mode):
        if mode == "channel_id":
            self.window_title.setText(T("#Search by Channel ID"))
            if len(self.db.settings.bookmarks) == 0:
                self.queryArea.setCurrentIndex(0)
            else:
                self.queryComboBox.addItems(self.db.settings.bookmarks)
                self.queryArea.setCurrentIndex(1)
        elif mode == "video_id":
            self.window_title.setText(T("#Search by Video / Clip ID"))
            self.queryArea.setCurrentIndex(0)
        else:
            self.window_title.setText(T("#Search by Channel / Video / Clip Link"))
            self.queryArea.setCurrentIndex(0)

class VideoFrame(QWidget, UiFiles.videoFrame):
    thumbnailImageLoaded = pyqtSignal(QPixmap)
    categoryImageLoaded = pyqtSignal(QPixmap)

    def __init__(self, db, data):
        super().__init__()
        self.db = db
        self.setupUi(self)
        self.videoType = type(data)
        self.thumbnail_image.setPixmap(QPixmap(Config.THUMBNAIL_IMAGE))
        self.category_image.setPixmap(QPixmap(Config.CATEGORY_IMAGE))
        self.thumbnailImageLoaded.connect(self.setThumbnailImage)
        self.categoryImageLoaded.connect(self.setCategoryImage)
        if self.videoType == TwitchGqlModels.Stream:
            self.stream = data
            self.setStreamInfo()
        elif self.videoType == TwitchGqlModels.Video:
            self.video = data
            self.setVideoInfo()
        else:
            self.clip = data
            self.setClipInfo()

    def setStreamInfo(self):
        self.title.setText(self.stream.title)
        self.title.setToolTip(self.stream.title)
        self.info_1.setText(self.stream.game.name)
        self.info_2.setText(str(self.stream.createdAt.toUTC(self.db.localization.timezone)))
        self.more.clicked.connect(self.showStreamInfo)
        self.loadThumbnailImage(self.stream.previewImageURL)
        self.loadCategoryImage(self.stream.game.boxArtURL)

    def setVideoInfo(self):
        self.title.setText(self.video.title)
        self.title.setToolTip(self.video.title)
        self.info_1.setText(str(self.video.publishedAt.toUTC(self.db.localization.timezone)))
        self.info_2.setText(str(self.video.lengthSeconds))
        self.more.clicked.connect(self.showVideoInfo)
        self.loadThumbnailImage(self.video.previewThumbnailURL)
        self.loadCategoryImage(self.video.game.boxArtURL)

    def setClipInfo(self):
        self.title.setText(self.clip.title)
        self.title.setToolTip(self.clip.title)
        self.info_1.setText(str(self.clip.createdAt.toUTC(self.db.localization.timezone)))
        self.info_2.setText(str(self.clip.durationSeconds))
        self.more.clicked.connect(self.showClipInfo)
        self.loadThumbnailImage(self.clip.thumbnailURL)
        self.loadCategoryImage(self.clip.game.boxArtURL)

    def setThumbnailImage(self, pixmap):
        self.thumbnail_image.setPixmap(pixmap)

    def setCategoryImage(self, pixmap):
        self.category_image.setPixmap(pixmap)

    def loadThumbnailImage(self, url):
        threading.Thread(target=self.thumbnailImageThread, args=(url,)).start()

    def loadCategoryImage(self, url):
        threading.Thread(target=self.categoryImageThread, args=(url,)).start()

    def thumbnailImageThread(self, url):
        image = Utils.Image(url, Config.THUMBNAIL_IMAGE)
        try:
            self.thumbnailImageLoaded.emit(image)
        except:
            pass

    def categoryImageThread(self, url):
        image = Utils.Image(url, Config.CATEGORY_IMAGE)
        try:
            self.categoryImageLoaded.emit(image)
        except:
            pass

    def showStreamInfo(self):
        kwargs = {
            "channel": self.stream.broadcaster.formattedName(),
            "title": self.stream.title,
            "game": self.stream.game.displayName,
            "startedAt": self.stream.createdAt.toUTC(self.db.localization.timezone),
            "viewer": self.stream.viewersCount
        }
        Utils.info("#Stream Information", "#Channel : {channel}\nTitle : {title}\nCategory : {game}\nStarted At : {startedAt}\nViewer Count : {viewer}", **kwargs)

    def showVideoInfo(self):
        kwargs = {
            "channel": self.video.owner.formattedName(),
            "title": self.video.title,
            "game": self.video.game.displayName,
            "duration": self.video.lengthSeconds,
            "publishedAt": self.video.publishedAt.toUTC(self.db.localization.timezone),
            "view": self.video.viewCount
        }
        Utils.info("#Video Information", "#Channel : {channel}\nTitle : {title}\nCategory : {game}\nDuration : {duration}\nPublished At : {publishedAt}\nView Count : {view}", **kwargs)

    def showClipInfo(self):
        kwargs = {
            "channel": self.clip.broadcaster.formattedName(),
            "title": self.clip.title,
            "game": self.clip.game.displayName,
            "creator": self.clip.curator.formattedName(),
            "duration": self.clip.durationSeconds,
            "createdAt": self.clip.createdAt.toUTC(self.db.localization.timezone),
            "view": self.clip.viewCount
        }
        Utils.info("#Clip Information", "#Channel : {channel}\nTitle : {title}\nCategory : {game}\nCreator : {creator}\nDuration : {duration}\nCreated At : {createdAt}\nView Count : {view}", **kwargs)

class VideoBox(QWidget, UiFiles.videoBox):
    def __init__(self, db, window, data):
        super().__init__()
        self.db = db
        self.setupUi(self)
        self.window = window
        self.data = data
        self.videoFrameArea.layout().addWidget(self.db.ui.VideoFrame(self.data))
        self.videoType = type(self.data)
        if self.videoType == TwitchGqlModels.Video:
            self.downloadButton.clicked.connect(self.downloadVideo)
        else:
            self.downloadButton.clicked.connect(self.downloadClip)

    def checkVideo(self):
        try:
            video = TwitchVod(self.data.id, self.db.account.user)
        except TokenError:
            try:
                self.db.account.user.reloadUser(self.db.api)
                Utils.info("authentication-error", "#An authentication error has occurred.\nIf the error persists, please log in again.")
            except:
                Utils.info("login-expired", "#Your login has expired.\nIf you do not log in again, the downloader will operate in a logged out state.")
            return False
        except:
            Utils.info("download-failed", "#A network error has occurred.")
            return False
        if video.found == False:
            Utils.info("unable-to-download", "#Video not found. Deleted or temporary error.")
            return False
        elif video.found == VodRestricted:
            if self.db.account.user.connected:
                advice = T("#Unable to find subscription in your account.\nSubscribe to this streamer or log in with another account.")
            else:
                advice = T("#You need to log in to download subscriber-only videos.")
            Utils.info("unable-to-download", "#This video is for subscribers only.\n{advice}", advice=advice)
            return False
        return video

    def checkClip(self):
        try:
            clip = TwitchClip(self.data.slug, self.db.account.user)
        except TokenError:
            try:
                self.db.account.user.reloadUser(self.db.api)
                Utils.info("authentication-error", "#An authentication error has occurred.\nIf the error persists, please log in again.")
            except:
                Utils.info("login-expired", "#Your login has expired.\nIf you do not log in again, the downloader will operate in a logged out state.")
            return False
        except:
            Utils.info("download-failed", "#A network error has occurred.")
            return False
        if clip.found == False:
            Utils.info("unable-to-download", "#Clip not found. Deleted or temporary error.")
            return False
        return clip

    def downloadVideo(self):
        self.downloadButton.setText(T("#Loading..."))
        self.downloadButton.repaint()
        videoToken = self.checkVideo()
        self.downloadButton.setText(T("download"))
        if videoToken == False:
            return
        self.db.setupDownload(self.data, videoToken)
        downloadMenu = self.db.ui.DownloadMenu(self.data, videoToken)
        if downloadMenu.exec():
            self.window.close()
        else:
            self.db.cancelDownload()
        del downloadMenu
        gc.collect()

    def downloadClip(self):
        self.downloadButton.setText(T("#Loading..."))
        self.downloadButton.repaint()
        clipToken = self.checkClip()
        self.downloadButton.setText(T("download"))
        if clipToken == False:
            return
        self.db.setupDownload(self.data, clipToken)
        downloadMenu = self.db.ui.DownloadMenu(self.data, clipToken)
        if downloadMenu.exec():
            if self.db.fileDownload["downloadType"] == "clip":
                self.window.setLoading(T("#Downloading..."), 0)
                self.db.downloadClip(self.window.progressSignal)
                self.window.setLoading(False)
            else:
                self.window.close()
        else:
            self.db.cancelDownload()
        del downloadMenu
        gc.collect()

class VideoList(QDialog, UiFiles.videoList):
    progressSignal = pyqtSignal(str, int)

    windowSize = {
        "small": {
            "window": (530, 760),
            "adSize": (0, 50),
            "previewSize": (480, 270),
            "layoutColumn": 1,
            "showAdSize": (320, 100)
        },
        "medium": {
            "window": (1000, 940),
            "adSize": (0, 50),
            "previewSize": (800, 450),
            "layoutColumn": 2,
            "showAdSize": (300, 250)
        },
        "large": {
            "window": (1300, 940),
            "adSize": (0, 50),
            "previewSize": (800, 450),
            "layoutColumn": 3,
            "showAdSize": (300, 250)
        }
    }

    class SizeMode:
        def __init__(self, name, data):
            self.sizeName = name
            self.windowSize = data["window"]
            self.adSize = data["adSize"]
            self.previewSize = data["previewSize"]
            self.layoutColumn = data["layoutColumn"]
            self.showAdSize = data["showAdSize"]

    DATA_LOAD_POSITION = 100

    searchTypes = [
        ("past-broadcasts", "ARCHIVE"),
        ("highlights", "HIGHLIGHT"),
        ("clips", None),
        ("uploads", "UPLOAD"),
        ("past-premiers", "PAST_PREMIERE"),
        ("all-videos", None)
    ]

    sortList = [
        ("date", "TIME"),
        ("popular", "VIEWS")
    ]

    filterList = [
        ("24h", "LAST_DAY"),
        ("7d", "LAST_WEEK"),
        ("30d", "LAST_MONTH"),
        ("all", "ALL_TIME")
    ]

    def __init__(self, db, mode, data):
        super().__init__()
        self.db = db
        self.setupUi(self)
        self.db.cancelDownload()
        self.sizeMode = self.SizeMode(self.db.temp.videoListWindowSize, self.windowSize[self.db.temp.videoListWindowSize])
        self.setup(mode, data)
        self.smallWindow.clicked.connect(lambda: self.setSizeMode("small"))
        self.mediumWindow.clicked.connect(lambda: self.setSizeMode("medium"))
        self.largeWindow.clicked.connect(lambda: self.setSizeMode("large"))
        self.reloadSize()

    def setSizeMode(self, mode):
        if self.sizeMode.sizeName != mode:
            self.sizeMode = self.SizeMode(mode, self.windowSize[mode])
            self.db.setVideoListWindowSize(mode)
            self.reloadSize()

    def reloadSize(self):
        if Config.SHOW_ADS:
            self.setFixedSize(self.sizeMode.windowSize[0], self.sizeMode.windowSize[1])
        else:
            self.setFixedSize(self.sizeMode.windowSize[0] - self.sizeMode.adSize[0], self.sizeMode.windowSize[1] - self.sizeMode.adSize[1])
        self.preview_image.setFixedSize(self.sizeMode.previewSize[0], self.sizeMode.previewSize[1])
        self.reloadSizeButtons()
        self.reloadVideoLayout()

    def reloadSizeButtons(self):
        if self.sizeMode.sizeName == "small":
            self.smallWindow.setEnabled(False)
            self.mediumWindow.setEnabled(True)
            self.largeWindow.setEnabled(True)
        elif self.sizeMode.sizeName == "medium":
            self.smallWindow.setEnabled(True)
            self.mediumWindow.setEnabled(False)
            self.largeWindow.setEnabled(True)
        else:
            self.smallWindow.setEnabled(True)
            self.mediumWindow.setEnabled(True)
            self.largeWindow.setEnabled(False)

    def setup(self, mode, data):
        if mode == "channel_id":
            self.window_title.setText(T("#{channel}'s channel", channel=data["channel"].displayName))
            self.setChannel(data["channel"])
            self.searchType.addItems(list(map(lambda item: T(item[0]), self.searchTypes)))
            self.searchType.setCurrentIndex(0)
            self.searchType.currentIndexChanged.connect(self.loadSortOrFilter)
            self.sortOrFilter.currentIndexChanged.connect(self.setSearchOptions)
            self.loadSortOrFilter(0)
        elif mode == "video_id":
            self.tabWidget.setTabEnabled(0, False)
            self.window_title.setText(T("#Video ID : {id}", id=data["video"].id))
            self.controlArea.hide()
            self.noResultsLabel.hide()
            self.clearVideoList()
            self.setVideoList([data["video"]])
        else:
            self.tabWidget.setTabEnabled(0, False)
            self.window_title.setText(T("#Clip ID : {id}", id=data["clip"].slug))
            self.controlArea.hide()
            self.noResultsLabel.hide()
            self.clearVideoList()
            self.setVideoList([data["clip"]])
        self.scrollArea.verticalScrollBar().valueChanged.connect(self.searchMoreVideos)
        self.progressSignal.connect(self.setLoading)
        self.setLoading(False)

    def loadSortOrFilter(self, index):
        self.sortOrFilter.clear()
        if self.searchTypes[index][0] == "clips":
            self.sortOrFilter.addItems(list(map(lambda item: T(item[0]), self.filterList)))
        else:
            self.sortOrFilter.addItems(list(map(lambda item: T(item[0]), self.sortList)))
        self.sortOrFilter.setCurrentIndex(0)

    def setSearchOptions(self, index):
        if index == -1:
            return
        searchType = self.searchTypes[self.searchType.currentIndex()][0]
        self.channelVideosLabel.setText(T("#{channel}'s {searchType}", channel=self.channel.displayName, searchType=T(searchType)))
        self.searchVideos()

    def searchVideos(self, cursor=""):
        self.setLoading(T("#Loading..."))
        self.statusArea.repaint()
        if self.searchTypes[self.searchType.currentIndex()][0] == "clips":
            filter = self.filterList[self.sortOrFilter.currentIndex()][1]
            try:
                self.searchResult = self.db.api.getChannelClips(self.channel.login, filter, Config.DATA_LOAD_LIMIT, cursor)
            except:
                Utils.info("error", "#A network error has occurred.")
                return
        else:
            type = self.searchTypes[self.searchType.currentIndex()][1]
            sort = self.sortList[self.sortOrFilter.currentIndex()][1]
            try:
                self.searchResult = self.db.api.getChannelVideos(self.channel.login, type, sort, Config.DATA_LOAD_LIMIT, cursor)
            except:
                Utils.info("error", "#A network error has occurred.")
                return
        if cursor == "":
            self.clearVideoList()
            if len(self.searchResult.data) == 0:
                self.videoArea.hide()
                self.noResultsLabel.show()
            else:
                self.videoArea.show()
                self.noResultsLabel.hide()
        self.setVideoList(self.searchResult.data)
        self.setLoading(False)

    def searchMoreVideos(self, value):
        if self.searchResult.hasNextPage:
            if (self.scrollArea.verticalScrollBar().maximum() - value) < self.DATA_LOAD_POSITION:
                self.searchVideos(self.searchResult.cursor)

    def setChannel(self, channel):
        self.channel = channel
        if channel.stream == None:
            self.liveLabel.setText(T("offline"))
            self.viewer_count.hide()
            self.preview_image.setPixmap(Utils.Image(channel.offlineImageURL, Config.OFFLINE_IMAGE))
            self.infoArea.hide()
            self.liveDownload.hide()
        else:
            stream = channel.stream
            self.liveLabel.setText(T("live"))
            self.viewer_count.setText(T("#{viewer} viewers", viewer=stream.viewersCount))
            self.preview_image.setPixmap(Utils.Image(stream.previewImageURL, Config.THUMBNAIL_IMAGE))
            self.category_image.setPixmap(Utils.Image(stream.game.boxArtURL, Config.CATEGORY_IMAGE))
            self.title.setText(stream.title)
            self.category.setText(stream.game.displayName)
            self.started_at.setText(str(stream.createdAt.toUTC(self.db.localization.timezone)))
            self.liveDownload.clicked.connect(self.downloadStream)
        self.profile_image.setPixmap(Utils.Image(channel.profileImageURL, Config.PROFILE_IMAGE))
        self.display_name.setText(channel.displayName)
        self.description.setText(channel.description)
        self.followers.setText(T("#{followers} followers", followers=channel.followers))
        if channel.isPartner:
            broadcasterType = "#Partner Streamer"
        elif channel.isAffiliate:
            broadcasterType = "#Affiliate Streamer"
        else:
            broadcasterType = "#Streamer"
        self.broadcaster_type.setText(T(broadcasterType))

    def setVideoList(self, videoList):
        for data in videoList:
            self.addLayoutWidget(self.db.ui.VideoBox(self, data))

    def clearVideoList(self):
        self.clearVideoLayout()
        self.layoutWidgets = []

    def addLayoutWidget(self, widget):
        self.layoutWidgets.append(widget)
        self.setLayoutWidget(len(self.layoutWidgets) - 1)
        if len(self.layoutWidgets) % 6 == 0:
            if Config.SHOW_ADS:
                self.addLayoutWidget(AdManager(self.sizeMode.showAdSize[0], self.sizeMode.showAdSize[1]))

    def setLayoutWidget(self, index):
        self.videoArea.layout().addWidget(self.layoutWidgets[index], index // self.sizeMode.layoutColumn, index % self.sizeMode.layoutColumn)

    def reloadVideoLayout(self):
        self.clearVideoLayout()
        for index in range(len(self.layoutWidgets)):
            self.setLayoutWidget(index)

    def clearVideoLayout(self):
        self.scrollArea.verticalScrollBar().setValue(0)
        layout = self.videoArea.layout()
        for index in range(layout.count()):
            layout.itemAt(0).widget().setParent(None)

    def checkStream(self):
        try:
            stream = TwitchStream(self.channel.login, self.db.account.user)
        except TokenError:
            try:
                self.db.account.user.reloadUser(self.db.api)
                Utils.info("authentication-error", "#An authentication error has occurred.\nIf the error persists, please log in again.")
            except:
                Utils.info("login-expired", "#Your login has expired.\nIf you do not log in again, the downloader will operate in a logged out state.")
            return False
        except:
            Utils.info("download-failed", "{error}\n{reason}", error=T("#A network error has occurred."), reason=T("#Temporary Error or Restricted Content"))
            return False
        if stream.found == False:
            Utils.info("unable-to-download", "#Channel not found. Deleted or temporary error.")
        elif stream.found == ChannelIsOffline:
            Utils.info("unable-to-download", "#Stream not found. Terminated or temporary error.")
            return False
        if stream.hideAds == False:
            if self.db.account.user.connected:
                if not Utils.ask("warning", "#Twitch's ads can't be blocked during the stream because your account doesn't have any subscription to this channel.\nProceed?"):
                    return False
            else:
                if not Utils.ask("warning", "#To block Twitch ads during the stream, you need to log in with your subscribed account.\nYou are currently not logged in and cannot block Twitch ads during the stream.\nProceed?"):
                    return False
        return stream

    def downloadStream(self):
        self.liveDownload.setText(T("#Loading..."))
        self.liveDownload.repaint()
        streamToken = self.checkStream()
        self.liveDownload.setText(T("live-download"))
        if streamToken == False:
            return
        self.db.setupDownload(self.channel.stream, streamToken)
        downloadMenu = self.db.ui.DownloadMenu(self.channel.stream, streamToken)
        if downloadMenu.exec():
            self.close()
        else:
            self.db.cancelDownload()
        del downloadMenu
        gc.collect()

    def setLoading(self, loading, progress=None):
        if loading == False:
            self.statusArea.hide()
        else:
            self.statusLabel.setText(loading)
            if progress == None:
                self.loadingProgress.hide()
            else:
                self.loadingProgress.setValue(progress)
                self.loadingProgress.show()
            self.statusArea.show()

class DownloadMenu(QDialog, UiFiles.downloadMenu):
    adSize = [0, 50]

    def __init__(self, db, dataModel, accessToken):
        super().__init__()
        self.db = db
        self.setupUi(self)
        self.dataModel = dataModel
        self.accessToken = accessToken
        self.videoFrameArea.layout().addWidget(self.db.ui.VideoFrame(dataModel))
        self.loadOptions()

    def keyPressEvent(self, event):
        if ((not event.modifiers() and event.key() == Qt.Key_Return) or (event.modifiers() == Qt.KeypadModifier and event.key() == Qt.Key_Enter)):
            event.accept()
        else:
            super().keyPressEvent(event)

    def loadOptions(self):
        self.window_title.setText(T("#Download {type}", type=T(self.accessToken.dataType)))
        self.currentDirectory.setText(self.db.fileDownload["saveDirectory"] + "/" + self.db.fileDownload["fileName"])
        self.currentDirectory.setCursorPosition(0)
        self.searchDirectory.clicked.connect(self.askSaveDirectory)
        self.resolution.addItems(self.accessToken.getResolutions())
        self.resolution.setCurrentIndex(0)
        self.resolution.currentIndexChanged.connect(self.db.setDownloadResolution)
        if self.accessToken.dataType == "stream":
            self.cropArea.hide()
            self.settings.clicked.connect(self.openSettings)
        elif self.accessToken.dataType == "video":
            self.setupCropArea()
            self.reloadCropArea()
            h, m, s = self.cropRange
            self.endSpinH.setValue(h)
            self.endSpinM.setValue(m)
            self.endSpinS.setValue(s)
            self.settings.clicked.connect(self.openSettings)
        else:
            self.cropArea.hide()
            self.settings.hide()

    def setupCropArea(self):
        self.cropArea.setTitle(T("#Crop / Total Length : {duration}", duration=self.dataModel.lengthSeconds))
        self.startCheckBox.stateChanged.connect(self.reloadCropBar)
        self.endCheckBox.stateChanged.connect(self.reloadCropBar)
        h, m, s = str(self.dataModel.lengthSeconds).split(":")
        self.cropRange = [int(h), int(m), int(s)]
        self.startSpinH.valueChanged.connect(self.reloadCropRange)
        self.startSpinM.valueChanged.connect(self.reloadCropRange)
        self.startSpinS.valueChanged.connect(self.reloadCropRange)
        self.endSpinH.valueChanged.connect(self.reloadCropRange)
        self.endSpinM.valueChanged.connect(self.reloadCropRange)
        self.endSpinS.valueChanged.connect(self.reloadCropRange)

    def reloadCropRange(self):
        h, m, s = self.cropRange
        self.startSpinH.setRange(0, h)
        if self.startSpinH.value() == h:
            self.startSpinM.setRange(0, m)
        else:
            self.startSpinM.setRange(0, 59)
        if self.startSpinM.value() == m:
            self.startSpinS.setRange(0, s)
        else:
            self.startSpinS.setRange(0, 59)
        self.endSpinH.setRange(0, h)
        if self.endSpinH.value() == h:
            self.endSpinM.setRange(0, m)
        else:
            self.endSpinM.setRange(0, 59)
        if self.endSpinM.value() == m:
            self.endSpinS.setRange(0, s)
        else:
            self.endSpinS.setRange(0, 59)

    def reloadCropBar(self):
        self.startTimeBar.setEnabled(not self.startCheckBox.isChecked())
        self.endTimeBar.setEnabled(not self.endCheckBox.isChecked())

    def reloadCropArea(self):
        self.reloadCropRange()
        self.reloadCropBar()
        if self.db.settings.engineType == "popcorn":
            self.cropArea.setEnabled(False)
            self.cropInfoLabel.setText(T("#Cropping is only supported in [Biscuit Engine]."))
        else:
            self.cropArea.setEnabled(True)
            self.cropInfoLabel.setText(T("#The crop is based on the nearest point in the crop range that can be processed."))

    def askSaveDirectory(self):
        directory = self.db.fileDownload["saveDirectory"] + "/" + self.db.fileDownload["fileName"]
        if self.accessToken.dataType == "clip":
            filters = T("#mp4 file (*.mp4)")
            initialFilter = "mp4"
        else:
            if self.db.settings.enableMp4:
                filters = T("#ts file (recommended) (*.ts);;mp4 file (*.mp4)")
            else:
                filters = T("#ts file (*.ts)")
            initialFilter = "ts"
        newDirectory = Utils.askSaveDirectory(self, directory, filters, initialFilter)
        if newDirectory != "":
            self.db.setFileSaveDirectory(newDirectory)
            self.currentDirectory.setText(newDirectory)
            self.currentDirectory.setCursorPosition(0)

    def accept(self):
        if self.accessToken.dataType == "video" and self.db.settings.engineType == "biscuit":
            if not self.validateCropRange():
                return
        if Utils.checkFileExists(self.db.fileDownload["saveDirectory"] + "/" + self.db.fileDownload["fileName"]):
            if not Utils.ask("overwrite", "#A file with the same name already exists.\nOverwrite?"):
                return
        super().accept()

    def validateCropRange(self):
        if self.saveCropRange():
            return True
        else:
            Utils.info("warning", "#The end point of the cropping range is equal to or earlier than the start point.")
            return False

    def saveCropRange(self):
        if self.startCheckBox.isChecked():
            start = None
        else:
            start = self.startSpinH.value() * 3600 + self.startSpinM.value() * 60 + self.startSpinS.value()
        if self.endCheckBox.isChecked():
            end = None
        else:
            end = self.endSpinH.value() * 3600 + self.endSpinM.value() * 60 + self.endSpinS.value()
        if start != None and end != None:
            if start >= end:
                return False
        self.db.setCropRange(start, end)
        return True

    def openSettings(self):
        self.db.mainWindow.openSettings()
        if self.accessToken.dataType == "video":
            self.reloadCropArea()

class Download(QWidget, UiFiles.download):
    adSize = [300, 100]

    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setupUi(self)
        if self.db.fileDownload["downloadType"] == "stream":
            self.accessToken = self.db.fileDownload["stream"]
        else:
            self.accessToken = self.db.fileDownload["video"]
        self.category_image.setPixmap(Utils.Image(self.accessToken.game.boxArtURL, Config.CATEGORY_IMAGE))
        self.category.setText(self.accessToken.game.displayName)
        self.title.setText(T("#Title : {title}", title=self.accessToken.title))
        self.title.setToolTip(self.accessToken.title)
        if self.db.fileDownload["downloadType"] == "stream":
            self.thumbnail_image.setPixmap(Utils.Image(self.accessToken.previewImageURL, Config.THUMBNAIL_IMAGE))
            self.user_name.setText(T("#Channel : {channel}", channel=self.accessToken.broadcaster.displayName))
            self.date.setText(T("#Date : {date}", date=self.accessToken.createdAt.toUTC(self.db.localization.timezone)))
            self.duration.setText(T("#Duration : {duration}", duration=T("unknown")))
            self.view_count.setText(T("#Viewer Count : {viewer}", viewer=self.accessToken.viewersCount))
        else:
            self.thumbnail_image.setPixmap(Utils.Image(self.accessToken.previewThumbnailURL, Config.THUMBNAIL_IMAGE))
            self.user_name.setText(T("#Channel : {channel}", channel=self.accessToken.owner.displayName))
            self.date.setText(T("#Date : {date}", date=self.accessToken.publishedAt.toUTC(self.db.localization.timezone)))
            start, end = self.db.fileDownload["range"]
            if start == None and end == None:
                self.duration.setText(T("#Duration : {duration}", duration=self.accessToken.lengthSeconds))
            else:
                if start == None:
                    start = T("#From start")
                else:
                    start = self.getTimeString(start)
                if end == None:
                    end = T("#To end")
                else:
                    end = self.getTimeString(end)
                self.duration.setText(T("#Duration : {duration} / Crop : {start} ~ {end}", duration=self.accessToken.lengthSeconds, start=start, end=end))
            self.view_count.setText(T("#View Count : {view}", view=self.accessToken.viewCount))
        self.resolution.setText(T("#Resolution : {resolution}", resolution=self.db.fileDownload["resolution"]))
        self.file.setText(T("#File : {file}", file=self.db.fileDownload["saveDirectory"] + "/" + self.db.fileDownload["fileName"]))
        self.file.setToolTip(self.db.fileDownload["saveDirectory"] + "/" + self.db.fileDownload["fileName"])
        self.cancelCompleteButtonArea.setCurrentIndex(0)
        self.cancelButton.clicked.connect(self.cancelDownload)
        self.completeButton.clicked.connect(self.db.mainWindow.startMainMenu)
        self.openFolderButton.clicked.connect(self.openFolder)
        self.openFileButton.clicked.connect(self.openFile)
        self.openFileButton.hide()
        self.status.setText(T("#Preparing..."))
        if self.db.fileDownload["downloadType"] == "stream":
            self.downloadProgressBar.setRange(0, 0)
        else:
            self.liveLabel.hide()
        self.downloader = Downloader(self.db)
        self.downloader.streamProgress.connect(self.streamProgress)
        self.downloader.videoProgress.connect(self.videoProgress)
        self.downloader.downloadComplete.connect(self.downloadComplete)
        self.downloader.errorOccurred.connect(self.errorOccurred)
        self.db.setDownloadingState(True)
        self.downloader.start()

    def getTimeString(self, totalSeconds):
        h = str(totalSeconds // 3600)
        h = (2 - len(h)) * "0" + h
        m = str(totalSeconds % 3600 // 60)
        m = (2 - len(m)) * "0" + m
        s = str(totalSeconds % 3600 % 60)
        s = (2 - len(s)) * "0" + s
        return h + ":" + m + ":" + s

    def streamProgress(self, complete, duration):
        if complete:
            self.downloadProgressBar.setRange(0, 100)
            self.encodingProgressBar.setRange(0, 100)
            self.downloadProgressBar.setValue(100)
            self.encodingProgressBar.setValue(100)
        else:
            self.status.setText(T("#Downloading Live Stream..."))
        self.currentDuration.setText(duration)

    def videoProgress(self, downloadProgress, encodingProgress, duration):
        if downloadProgress == -1:
            self.status.setText(T("#Waiting for download... / Checking for additional files (5 minutes)"))
            self.downloadProgressBar.setRange(0, 0)
        else:
            self.status.setText(T("#Downloading..."))
            self.downloadProgressBar.setRange(0, 100)
            self.downloadProgressBar.setValue(downloadProgress)
        self.encodingProgressBar.setValue(encodingProgress)
        self.currentDuration.setText(duration)

    def cancelDownload(self):
        if Utils.ask("cancel-download", "#Are you sure you want to cancel the download?"):
            self.cancelButton.setText(T("#Canceling..."))
            self.repaint()
            if self.downloader.cancelDownload() == False:
                Utils.info("notification", "#The download has already been completed.")

    def downloadComplete(self, complete):
        if complete:
            self.window_title.setText(T("download-complete"))
            self.status.setText(T("download-complete"))
            self.openFileButton.show()
        else:
            self.window_title.setText(T("download-canceled"))
            self.status.setText(T("download-canceled"))
        self.cancelCompleteButtonArea.setCurrentIndex(1)
        self.db.setDownloadingState(False)
        if complete:
            if self.db.settings.autoClose:
                self.db.forceClose()
            else:
                Utils.info("download-complete", "#Download completed.")

    def errorOccurred(self):
        Utils.info("error", "#An error occurred while downloading.")

    def openFolder(self):
        try:
            os.startfile(self.db.fileDownload["saveDirectory"])
        except:
            Utils.info("error", "#Folder not found.\nIt has been moved, renamed or deleted.")

    def openFile(self):
        try:
            os.startfile(self.db.fileDownload["saveDirectory"] + "/" + self.db.fileDownload["fileName"])
        except:
            Utils.info("error", "#File not found.\nIt has been moved, renamed or deleted.")

class Downloader(QThread):
    streamProgress = pyqtSignal(bool, str)
    videoProgress = pyqtSignal(int, int, str)
    downloadComplete = pyqtSignal(bool)
    errorOccurred = pyqtSignal()

    def __init__(self, db):
        super().__init__()
        self.db = db
        if self.db.fileDownload["downloadType"] == "stream":
            self.url = self.db.fileDownload["streamData"].resolution(self.db.fileDownload["resolution"]).url
        else:
            self.url = self.db.fileDownload["videoData"].resolution(self.db.fileDownload["resolution"]).url
        self.fileName = self.db.fileDownload["saveDirectory"] + "/" + self.db.fileDownload["fileName"]

    def run(self):
        self.startDownload()

    def startDownload(self):
        ffmpeg = Config.DEPENDENCIES_ROOT + "/ffmpeg.exe"
        try:
            if self.db.fileDownload["downloadType"] == "video" and self.db.settings.engineType == "popcorn":
                data_path = self.db.temp.tempDirectory + "/" + self.db.fileDownload["video"].id
                Utils.createDirectory(data_path)
                self.downloader = TwitchDownloaderPopcornEngine(ffmpeg, self.url, self.fileName, data_path, self.db.engines.popcorn.fastDownload, self.db.engines.popcorn.updateTracking)
            else:
                self.downloader = TwitchDownloaderBiscuitEngine(ffmpeg, self.db.fileDownload["downloadType"], self.url, self.fileName)
                if self.db.fileDownload["downloadType"] == "video":
                    start, end = self.db.fileDownload["range"]
                    self.downloader.setRange(start, end)
        except:
            self.videoProgress.emit(100, 100, "{time} / {time}".format(time=T("unknown")))
            self.downloadComplete.emit(False)
            self.errorOccurred.emit()
            return
        self.downloader.download()
        if self.db.fileDownload["downloadType"] == "stream":
            while self.downloader.done == False:
                self.streamProgress.emit(False, self.downloader.timeProgress)
                time.sleep(1)
            self.streamProgress.emit(True, self.downloader.timeProgress)
            if self.downloader.canceled:
                self.downloadComplete.emit(False)
                if self.downloader.error:
                    self.errorOccurred.emit()
            else:
                self.downloadComplete.emit(True)
        else:
            while self.downloader.done == False:
                downloadProgress = (self.downloader.fileProgress / self.downloader.totalFiles) * 100
                encodingProgress = (Utils.getTotalSeconds(self.downloader.timeProgress) / self.downloader.totalSeconds) * 100
                duration = self.downloader.timeProgress + " / " + self.downloader.totalTime
                if self.db.settings.engineType == "popcorn":
                    if self.downloader.waiting:
                        self.videoProgress.emit(-1, encodingProgress, duration)
                    else:
                        self.videoProgress.emit(downloadProgress, encodingProgress, duration)
                else:
                    self.videoProgress.emit(downloadProgress, encodingProgress, duration)
                time.sleep(1)
            if self.downloader.canceled:
                self.videoProgress.emit(100, 100, self.downloader.timeProgress + " / " + self.downloader.timeProgress)
                self.downloadComplete.emit(False)
                if self.downloader.error:
                    self.errorOccurred.emit()
            else:
                self.videoProgress.emit(100, 100, self.downloader.totalTime + " / " + self.downloader.totalTime)
                self.downloadComplete.emit(True)

    def cancelDownload(self):
        if self.downloader.done:
            return False
        else:
            self.downloader.cancelDownload()
            return True