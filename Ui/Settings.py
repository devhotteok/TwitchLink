from Core.Ui import *
from Services.Image.Loader import ImageLoader
from Download.Downloader.Engine.Config import Config as EngineConfig
from Download.DownloadManager import DownloadManager


class Settings(QtWidgets.QWidget, UiFile.settings):
    restartRequired = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(Settings, self).__init__(parent=parent)
        self.openProgressWindow.setChecked(DB.general.isOpenProgressWindowEnabled())
        self.openProgressWindow.toggled.connect(DB.general.setOpenProgressWindowEnabled)
        self.notify.setChecked(DB.general.isNotifyEnabled())
        self.notify.toggled.connect(DB.general.setNotifyEnabled)
        self.streamFilename.setText(DB.templates.getStreamFilename())
        self.streamFilename.editingFinished.connect(self.setStreamFilename)
        self.streamTemplateInfo.clicked.connect(self.showStreamTemplateInfo)
        self.videoFilename.setText(DB.templates.getVideoFilename())
        self.videoFilename.editingFinished.connect(self.setVideoFilename)
        self.videoTemplateInfo.clicked.connect(self.showVideoTemplateInfo)
        self.clipFilename.setText(DB.templates.getClipFilename())
        self.clipFilename.editingFinished.connect(self.setClipFilename)
        self.clipTemplateInfo.clicked.connect(self.showClipTemplateInfo)
        for bookmark in DB.general.getBookmarks():
            self.addBookmark(bookmark)
        self.bookmarkList.model().rowsInserted.connect(self.saveBookmark)
        self.bookmarkList.model().rowsMoved.connect(self.saveBookmark)
        self.bookmarkList.model().rowsRemoved.connect(self.saveBookmark)
        self.newBookmark.returnPressed.connect(self.tryAddBookmark)
        self.newBookmark.textChanged.connect(self.reloadBookmarkArea)
        self.addBookmarkButton.clicked.connect(self.tryAddBookmark)
        self.removeBookmarkButton.clicked.connect(self.removeBookmark)
        self.useExternalContentUrl.setChecked(DB.advanced.isExternalContentUrlEnabled())
        self.useExternalContentUrl.toggled.connect(DB.advanced.setExternalContentUrlEnabled)
        self.useExternalContentUrlInfo.clicked.connect(self.showExternalContentUrlInfo)
        self.useCaching.setChecked(DB.advanced.isCachingEnabled())
        self.useCaching.toggled.connect(DB.advanced.setCachingEnabled)
        self.useCachingInfo.clicked.connect(self.showCachingInfo)
        self.language.addItems(Translator.getLanguageList())
        self.language.setCurrentIndex(Translator.getLanguageKeyList().index(DB.localization.getLanguage()))
        self.language.currentIndexChanged.connect(self.setLanguage)
        self.timezone.addItems(DB.localization.getTimezoneList())
        self.timezone.setCurrentText(DB.localization.getTimezone().zone)
        self.timezone.currentTextChanged.connect(self.setTimezone)
        self.recommendedSpeed.setText(EngineConfig.RECOMMENDED_THREAD_LIMIT)
        self.downloadSpeed.setRange(1, EngineConfig.MAX_THREAD_LIMIT)
        self.downloadSpeed.valueChanged.connect(self.setDownloadSpeed)
        self.speedSpinBox.setRange(1, EngineConfig.MAX_THREAD_LIMIT)
        self.speedSpinBox.valueChanged.connect(self.setDownloadSpeed)
        self.setDownloadSpeed(DB.download.getDownloadSpeed())
        self.downloadSpeedStreamInfoIcon = Utils.setSvgIcon(self.downloadSpeedStreamInfoIcon, Icons.INFO_ICON)
        self.resetButton.clicked.connect(self.resetSettings)
        self.reloadBookmarkArea()
        DownloadManager.runningCountChangedSignal.connect(self.reload)
        self.reload()

    def reload(self):
        if DownloadManager.isDownloaderRunning():
            self.languageArea.setEnabled(False)
            self.timezoneArea.setEnabled(False)
            self.resetArea.setEnabled(False)
            self.restrictedLabel.show()
            ImageLoader.throttle(True)
        else:
            self.languageArea.setEnabled(True)
            self.timezoneArea.setEnabled(True)
            self.resetArea.setEnabled(True)
            self.restrictedLabel.hide()
            ImageLoader.throttle(False)

    def setStreamFilename(self):
        DB.templates.setStreamFilename(self.streamFilename.text())

    def setVideoFilename(self):
        DB.templates.setVideoFilename(self.videoFilename.text())

    def setClipFilename(self):
        DB.templates.setClipFilename(self.clipFilename.text())

    def getFormData(self, *args):
        formData = {}
        for data in args:
            formData.update(data)
        return formData

    def getInfoTitle(self, dataType):
        return f"{T(dataType)} {T('#Filename Template Variables')}"

    def getBaseInfo(self, dataType):
        dataType = T(dataType)
        return {
            "{type}": f"{T('file-type')} ({dataType})",
            "{id}": f"{dataType} {T('id')} (XXXXXXXXXX)",
            "{title}": "title",
            "{game}": "category"
        }

    def getResolutionInfo(self):
        return {
            "{resolution}": "file-resolution"
        }

    def getNameInfo(self, nameType):
        translated = T(nameType)
        return {
            f"{{{nameType}}}": f"{translated} {T('username')}",
            f"{{{nameType}_name}}": f"{translated} {T('displayname')}",
            f"{{{nameType}_formatted_name}}": T("#'displayname' if {nameType} Displayname is English, otherwise 'username(displayname)'", nameType=translated)
        }

    def getTimeInfo(self, timeType):
        return {
            f"{{{timeType}_at}}": f"{T(f'{timeType}-at')} (XXXX-XX-XX XX:XX:XX)",
            "{date}": f"{T(f'{timeType}-date')} (XXXX-XX-XX)",
            "{time}": f"{T(f'{timeType}-time')} (XX:XX:XX)"
        }

    def showStreamTemplateInfo(self):
        Ui.PropertyView(
            self.getInfoTitle("stream"),
            None,
            self.getFormData(
                self.getBaseInfo("stream"),
                self.getNameInfo("channel"),
                self.getTimeInfo("started"),
                self.getResolutionInfo()
            ),
            enableLabelSelection=True,
            enableFieldTranslation=True,
            parent=self
        ).exec()

    def showVideoTemplateInfo(self):
        Ui.PropertyView(
            self.getInfoTitle("video"),
            None,
            self.getFormData(
                self.getBaseInfo("video"),
                self.getNameInfo("channel"),
                {
                    "{duration}": "duration"
                },
                self.getTimeInfo("published"),
                {
                    "{views}": "views"
                },
                self.getResolutionInfo()
            ),
            enableLabelSelection=True,
            enableFieldTranslation=True,
            parent=self
        ).exec()

    def showClipTemplateInfo(self):
        Ui.PropertyView(
            self.getInfoTitle("clip"),
            None,
            self.getFormData(
                self.getBaseInfo("clip"),
                {
                    "{slug}": f"{T('slug')} (SlugExampleHelloTwitch)"
                },
                self.getNameInfo("channel"),
                self.getNameInfo("creator"),
                {
                    "{duration}": "duration"
                },
                self.getTimeInfo("created"),
                {
                    "{views}": "views"
                },
                self.getResolutionInfo()
            ),
            enableLabelSelection=True,
            enableFieldTranslation=True,
            parent=self
        ).exec()

    def reloadBookmarkArea(self):
        selected = self.bookmarkList.currentRow() != -1
        text = self.newBookmark.text().strip().lower()
        textNotEmptyOrDuplicate = text != "" and len(self.bookmarkList.findItems(text, QtCore.Qt.MatchFixedString)) == 0
        self.addBookmarkButton.setEnabled(textNotEmptyOrDuplicate)
        self.removeBookmarkButton.setEnabled(selected)

    def tryAddBookmark(self):
        if self.addBookmarkButton.isEnabled():
            self.addBookmark(self.newBookmark.text().strip().lower())
            self.newBookmark.clear()

    def addBookmark(self, bookmark):
        item = QtWidgets.QListWidgetItem(bookmark)
        item.setIcon(QtGui.QIcon(Icons.MOVE_ICON))
        item.setToolTip(T("#Drag to change order."))
        self.bookmarkList.addItem(item)
        self.newBookmark.clear()

    def removeBookmark(self):
        self.bookmarkList.takeItem(self.bookmarkList.currentRow())
        self.bookmarkList.setCurrentRow(-1)

    def saveBookmark(self):
        DB.general.setBookmarks([self.bookmarkList.item(index).text() for index in range(self.bookmarkList.count())])

    def showExternalContentUrlInfo(self):
        self.info("information", "#Recognize external content in URL search.\nStreamers or editors can download private videos from their dashboard.\nYou can download content outside of Twitch.")

    def showCachingInfo(self):
        self.info("information", "#Caches images for faster retrieval next time, but consumes a lot of memory(RAM).")

    def setLanguage(self, index):
        DB.localization.setLanguage(Translator.getLanguageCode(index))
        self.info("restart", "#Restart due to language change.")
        self.requestRestart()

    def setTimezone(self, timezone):
        DB.localization.setTimezone(timezone)
        self.info("restart", "#Restart due to time zone change.")
        self.requestRestart()

    def setDownloadSpeed(self, speed):
        DB.download.setDownloadSpeed(speed)
        self.downloadSpeed.setValueSilent(speed)
        self.speedSpinBox.setValueSilent(speed)

    def resetSettings(self):
        if self.ask("reset-settings", "#This will reset all settings.\nProceed?"):
            DB.reset()
            self.requestRestart()

    def requestRestart(self):
        self.restartRequired.emit()