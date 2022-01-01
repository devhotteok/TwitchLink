from Core.App import App
from Core.Ui import *
from Download.DownloadManager import DownloadManager
from Download.Downloader.Task.Config import Config as TaskConfig


class Settings(QtWidgets.QDialog, UiFile.settings):
    def __init__(self, page=0):
        super().__init__(parent=App.getActiveWindow())
        self.ignoreKey(QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter)
        self.autoClose.setChecked(DB.general.isAutoCloseEnabled())
        self.streamFilename.setText(DB.templates.getStreamFilename())
        self.videoFilename.setText(DB.templates.getVideoFilename())
        self.clipFilename.setText(DB.templates.getClipFilename())
        self.streamTemplateInfo.clicked.connect(self.showStreamTemplateInfo)
        self.videoTemplateInfo.clicked.connect(self.showVideoTemplateInfo)
        self.clipTemplateInfo.clicked.connect(self.showClipTemplateInfo)
        self.bookmarkList.addItems(DB.general.getBookmarks())
        self.bookmarkList.itemSelectionChanged.connect(self.reloadButtons)
        self.newBookmark.returnPressed.connect(self.addBookmark)
        self.newBookmark.textChanged.connect(self.reloadButtons)
        self.addBookmarkButton.clicked.connect(self.addBookmark)
        self.insertBookmarkButton.clicked.connect(self.insertBookmark)
        self.removeBookmarkButton.clicked.connect(self.removeBookmark)
        self.language.addItems(Translator.getLanguageList())
        self.language.setCurrentIndex(Translator.getLanguageKeyList().index(DB.localization.getLanguage()))
        self.language.currentIndexChanged.connect(self.setLanguage)
        self.timezone.addItems(DB.localization.getTimezoneList())
        self.timezone.setCurrentIndex(DB.localization.getTimezoneIndex())
        self.timezone.currentIndexChanged.connect(self.setTimezone)
        self.downloadEngineInfo.setHtml(Utils.getDocs("DownloadEngine", DB.localization.getLanguage()))
        self.downloadSpeed.valueChanged.connect(self.setDownloadSpeed)
        self.downloadSpeed.setRange(1, TaskConfig.MAX_THREAD_LIMIT)
        self.speedSpinBox.valueChanged.connect(self.setDownloadSpeed)
        self.speedSpinBox.setRange(1, TaskConfig.MAX_THREAD_LIMIT)
        self.setDownloadSpeed(DB.download.getDownloadSpeed())
        self.recommendedSpeed.setText(TaskConfig.RECOMMENDED_THREAD_LIMIT)
        self.unmuteVideo.setChecked(DB.download.isUnmuteVideoEnabled())
        self.updateTrack.setChecked(DB.download.isUpdateTrackEnabled())
        if DownloadManager.isDownloaderRunning():
            self.languageArea.setEnabled(False)
            self.timezoneArea.setEnabled(False)
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset).setEnabled(False)
        else:
            self.restrictedLabel.hide()
            self.changesInfoLabel.hide()
        self.buttonBox.accepted.connect(self.saveSettings)
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Reset).clicked.connect(self.resetSettings)
        self.tabWidget.setCurrentIndex(page)
        self.reloadButtons()

    def getFormData(self, *args):
        formData = {}
        for data in args:
            formData.update(data)
        return formData

    def getInfoTitle(self, dataType):
        return "{} {}".format(T(dataType), T("#Filename Template Variables"))

    def getBaseInfo(self, dataType):
        dataType = T(dataType)
        return {
            "{type}": "{} ({})".format(T("file-type"), dataType),
            "{id}": "{} {} (XXXXXXXXXX)".format(dataType, T("id")),
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
            "{{{}}}".format(nameType): "{} {}".format(translated, T("username")),
            "{{{}_name}}".format(nameType): "{} {}".format(translated, T("displayname")),
            "{{{}_formatted_name}}".format(nameType): T("#'displayname' if {nameType} Displayname is English, otherwise 'username(displayname)'", nameType=translated)
        }

    def getTimeInfo(self, timeType):
        return {
            "{{{}_at}}".format(timeType): "{} (XXXX-XX-XX XX:XX:XX)".format(T("{}-at".format(timeType))),
            "{date}": "{} (XXXX-XX-XX)".format(T("{}-date".format(timeType))),
            "{time}": "{} (XX:XX:XX)".format(T("{}-time".format(timeType)))
        }

    def showStreamTemplateInfo(self):
        Ui.FormInfo(
            self.getInfoTitle("stream"),
            None,
            self.getFormData(
                self.getBaseInfo("stream"),
                self.getNameInfo("channel"),
                self.getTimeInfo("started"),
                self.getResolutionInfo()
            ),
            enableLabelSelection=True,
            enableFieldTranslation=True
        ).exec()

    def showVideoTemplateInfo(self):
        Ui.FormInfo(
            self.getInfoTitle("video"),
            None,
            self.getFormData(
                self.getBaseInfo("video"),
                self.getNameInfo("channel"),
                {
                    "{duration}": "duration"
                },
                self.getTimeInfo("started"),
                {
                    "{views}": "views"
                },
                self.getResolutionInfo()
            ),
            enableLabelSelection=True,
            enableFieldTranslation=True
        ).exec()

    def showClipTemplateInfo(self):
        Ui.FormInfo(
            self.getInfoTitle("clip"),
            None,
            self.getFormData(
                self.getBaseInfo("clip"),
                {
                    "{slug}": "{} (SlugExampleHelloTwitch)".format(T("slug"))
                },
                self.getNameInfo("channel"),
                self.getNameInfo("creator"),
                {
                    "{duration}": "duration"
                },
                self.getTimeInfo("started"),
                {
                    "{views}": "views"
                },
                self.getResolutionInfo()
            ),
            enableLabelSelection=True,
            enableFieldTranslation=True
        ).exec()

    def reloadButtons(self):
        selected = self.bookmarkList.currentRow() != -1
        text = self.newBookmark.text().strip().lower()
        textNotEmptyOrDuplicate = text != "" and len(self.bookmarkList.findItems(text, QtCore.Qt.MatchFixedString)) == 0
        self.addBookmarkButton.setEnabled(textNotEmptyOrDuplicate)
        self.insertBookmarkButton.setEnabled(textNotEmptyOrDuplicate and selected)
        self.removeBookmarkButton.setEnabled(selected)

    def addBookmark(self):
        if self.addBookmarkButton.isEnabled():
            self.bookmarkList.addItem(self.newBookmark.text().strip().lower())
            self.newBookmark.clear()

    def insertBookmark(self):
        self.bookmarkList.insertItem(self.bookmarkList.currentRow(), self.newBookmark.text().strip().lower())
        self.bookmarkList.setCurrentRow(-1)
        self.newBookmark.clear()

    def removeBookmark(self):
        self.bookmarkList.takeItem(self.bookmarkList.currentRow())
        self.bookmarkList.setCurrentRow(-1)

    def setLanguage(self, index):
        self.saveSettings()
        DB.localization.setLanguage(Translator.getLanguageCode(index))
        Utils.info("restart", "#Restart due to language change.")
        App.restart()

    def setTimezone(self, index):
        self.saveSettings()
        DB.localization.setTimezoneNo(index)
        Utils.info("restart", "#Restart due to time zone change.")
        App.restart()

    def setDownloadSpeed(self, speed):
        self.downloadSpeed.setValue(speed)
        self.speedSpinBox.setValue(speed)

    def saveSettings(self, checkChanges=False):
        autoClose = self.autoClose.isChecked()
        streamFilename = self.streamFilename.text()
        videoFilename = self.videoFilename.text()
        clipFilename = self.clipFilename.text()
        bookmarks = []
        for index in range(self.bookmarkList.count()):
            bookmarks.append(self.bookmarkList.item(index).text())
        downloadSpeed = self.downloadSpeed.value()
        unmuteVideo = self.unmuteVideo.isChecked()
        updateTrack = self.updateTrack.isChecked()
        if checkChanges:
            return not (
                autoClose == DB.general.isAutoCloseEnabled() and
                bookmarks == DB.general.getBookmarks() and
                streamFilename == DB.templates.getStreamFilename() and
                videoFilename == DB.templates.getVideoFilename() and
                clipFilename == DB.templates.getClipFilename() and
                downloadSpeed == DB.download.getDownloadSpeed() and
                unmuteVideo == DB.download.isUnmuteVideoEnabled() and
                updateTrack == DB.download.isUpdateTrackEnabled()
            )
        else:
            DB.general.setAutoCloseEnabled(autoClose)
            DB.general.setBookmarks(bookmarks)
            DB.templates.setStreamFilename(streamFilename)
            DB.templates.setVideoFilename(videoFilename)
            DB.templates.setClipFilename(clipFilename)
            DB.download.setDownloadSpeed(downloadSpeed)
            DB.download.setUnmuteVideoEnabled(unmuteVideo)
            DB.download.setUpdateTrackEnabled(updateTrack)

    def resetSettings(self):
        if Utils.ask("reset-settings", "#This will reset all settings.\nProceed?"):
            DB.reset()
            App.restart()

    def reject(self):
        if self.saveSettings(checkChanges=True):
            if not Utils.ask("discard-changes", "#There are unsaved changes.\nDo you want to discard them?"):
                return
        return super().reject()