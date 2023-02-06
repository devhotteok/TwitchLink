from Core.Ui import *
from Services.Image.Loader import ImageLoader
from Download.Downloader.Engine.ThreadPool import DownloadThreadPool
from Download.Downloader.Engine.Config import Config as DownloadEngineConfig
from Download.GlobalDownloadManager import GlobalDownloadManager
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator


class Settings(QtWidgets.QWidget, UiFile.settings):
    restartRequired = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(Settings, self).__init__(parent=parent)
        self.openProgressWindow.setChecked(DB.general.isOpenProgressWindowEnabled())
        self.openProgressWindow.toggled.connect(DB.general.setOpenProgressWindowEnabled)
        self.notify.setChecked(DB.general.isNotifyEnabled())
        self.notify.toggled.connect(DB.general.setNotifyEnabled)
        self.confirmExit.setChecked(DB.general.isConfirmExitEnabled())
        self.confirmExit.toggled.connect(DB.general.setConfirmExitEnabled)
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
        self.bookmarkList.currentRowChanged.connect(self.reloadBookmarkArea)
        self.newBookmark.returnPressed.connect(self.tryAddBookmark)
        self.newBookmark.textChanged.connect(self.reloadBookmarkArea)
        self.addBookmarkButton.clicked.connect(self.tryAddBookmark)
        self.removeBookmarkButton.clicked.connect(self.removeBookmark)
        self.searchExternalContent.setChecked(DB.advanced.isSearchExternalContentEnabled())
        self.searchExternalContent.toggled.connect(DB.advanced.setSearchExternalContentEnabled)
        self.searchExternalContentInfo.clicked.connect(self.showSearchExternalContentInfo)
        self.useCaching.setChecked(ImageLoader.isCachingEnabled())
        self.useCaching.toggled.connect(ImageLoader.setCachingEnabled)
        self.useCachingInfo.clicked.connect(self.showCachingInfo)
        self.language.addItems(Translator.getLanguageList())
        self.language.setCurrentIndex(Translator.getLanguageKeyList().index(Translator.getLanguage()))
        self.language.currentIndexChanged.connect(self.setLanguage)
        self.timezone.addItems(DB.localization.getTimezoneNameList())
        self.timezone.setCurrentText(DB.localization.getTimezone().name())
        self.timezone.currentTextChanged.connect(self.setTimezone)
        self.recommendedSpeed.setText(DownloadEngineConfig.RECOMMENDED_THREAD_LIMIT)
        self.downloadSpeed.setRange(1, DownloadEngineConfig.MAX_THREAD_LIMIT)
        self.downloadSpeed.valueChanged.connect(self.setDownloadSpeed)
        self.speedSpinBox.setRange(1, DownloadEngineConfig.MAX_THREAD_LIMIT)
        self.speedSpinBox.valueChanged.connect(self.setDownloadSpeed)
        self.setDownloadSpeed(DownloadThreadPool.maxThreadCount())
        self.downloadSpeedStreamInfoIcon = Utils.setSvgIcon(self.downloadSpeedStreamInfoIcon, Icons.INFO_ICON)
        self.resetButton.clicked.connect(self.resetSettings)
        self.reloadBookmarkArea()
        GlobalDownloadManager.runningCountChangedSignal.connect(self.reload)
        self.reload()

    def reload(self):
        if GlobalDownloadManager.isDownloaderRunning():
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

    def showStreamTemplateInfo(self):
        Ui.PropertyView(
            FileNameGenerator.getInfoTitle("stream"),
            None,
            FileNameGenerator.getStreamFileNameTemplateFormData(),
            enableLabelSelection=True,
            enableFieldTranslation=True,
            parent=self
        ).exec()

    def showVideoTemplateInfo(self):
        Ui.PropertyView(
            FileNameGenerator.getInfoTitle("video"),
            None,
            FileNameGenerator.getVideoFileNameTemplateFormData(),
            enableLabelSelection=True,
            enableFieldTranslation=True,
            parent=self
        ).exec()

    def showClipTemplateInfo(self):
        Ui.PropertyView(
            FileNameGenerator.getInfoTitle("clip"),
            None,
            FileNameGenerator.getClipFileNameTemplateFormData(),
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

    def showSearchExternalContentInfo(self):
        self.info("information", "#Allow URL Search to retrieve external content.\nStreamers or editors can download private videos from their dashboard.\nYou can download content outside of Twitch.")

    def showCachingInfo(self):
        self.info("information", "#Caches images for faster retrieval next time, but consumes a lot of memory(RAM).")

    def setLanguage(self, index):
        Translator.setLanguage(Translator.getLanguageCode(index))
        self.requestRestart()

    def setTimezone(self, timezone):
        DB.localization.setTimezone(bytes(timezone, encoding="utf-8"))
        self.requestRestart()

    def setDownloadSpeed(self, speed):
        DownloadThreadPool.setMaxThreadCount(speed)
        self.downloadSpeed.setValueSilent(speed)
        self.speedSpinBox.setValueSilent(speed)

    def resetSettings(self):
        if self.ask("warning", "#This will reset all settings.\nProceed?"):
            DB.reset()
            self.requestRestart()

    def requestRestart(self):
        self.restartRequired.emit()