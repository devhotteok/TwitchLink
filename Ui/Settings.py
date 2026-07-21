from Core.Ui import *
from Download.Downloader.Core.Engine.Config import Config as DownloadEngineConfig
from Ui.Components.Widgets.FileNameTemplateInfo import FileNameTemplateInfo


class Settings(QtWidgets.QWidget):
    restartRequired = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("settings", self)
        self._ui.openProgressWindow.setChecked(App.Preferences.general.isOpenProgressWindowEnabled())
        self._ui.openProgressWindow.toggled.connect(App.Preferences.general.setOpenProgressWindowEnabled)
        self._ui.notify.setChecked(App.Preferences.general.isNotifyEnabled())
        self._ui.notify.toggled.connect(App.Preferences.general.setNotifyEnabled)
        self._ui.createSubfolderForDownloads.setChecked(App.Preferences.download.isCreateSubfolderForDownloadsEnabled())
        self._ui.createSubfolderForDownloads.toggled.connect(App.Preferences.download.setCreateSubfolderForDownloadsEnabled)
        self._ui.windowClose.setCurrentIndex(1 if App.Preferences.general.isSystemTrayEnabled() else 0)
        self._ui.windowClose.currentIndexChanged.connect(self.windowCloseChanged)
        if not Utils.isMinimizeToSystemTraySupported():
            self._ui.windowCloseArea.hide()
            
        self._ui.defaultDirectory.setText(App.Preferences.general.getDefaultDirectory())
        self._ui.defaultDirectory.editingFinished.connect(self.setDefaultDirectoryFromLineEdit)
        self._ui.searchDefaultDirectory.clicked.connect(self.askDefaultDirectory)
        
        self.streamTemplateInfoWindow = FileNameTemplateInfo(FileNameTemplateInfo.TYPE.STREAM, parent=self)
        self._ui.streamFilename.setText(App.Preferences.templates.getStreamFilename())
        self._ui.streamFilename.editingFinished.connect(self.setStreamFilename)
        self._ui.streamTemplateInfo.clicked.connect(self.streamTemplateInfoWindow.show)
        Utils.setIconViewer(self._ui.streamTemplateInfo, Icons.HELP)
        self.videoTemplateInfoWindow = FileNameTemplateInfo(FileNameTemplateInfo.TYPE.VIDEO, parent=self)
        self._ui.videoFilename.setText(App.Preferences.templates.getVideoFilename())
        self._ui.videoFilename.editingFinished.connect(self.setVideoFilename)
        self._ui.videoTemplateInfo.clicked.connect(self.videoTemplateInfoWindow.show)
        Utils.setIconViewer(self._ui.videoTemplateInfo, Icons.HELP)
        self.clipTemplateInfoWindow = FileNameTemplateInfo(FileNameTemplateInfo.TYPE.CLIP, parent=self)
        self._ui.clipFilename.setText(App.Preferences.templates.getClipFilename())
        self._ui.clipFilename.editingFinished.connect(self.setClipFilename)
        self._ui.clipTemplateInfo.clicked.connect(self.clipTemplateInfoWindow.show)
        Utils.setIconViewer(self._ui.clipTemplateInfo, Icons.HELP)
        for bookmark in App.Preferences.general.getBookmarks():
            self.addBookmark(bookmark)
        self._ui.bookmarkList.model().rowsInserted.connect(self.saveBookmark)
        self._ui.bookmarkList.model().rowsMoved.connect(self.saveBookmark)
        self._ui.bookmarkList.model().rowsRemoved.connect(self.saveBookmark)
        self._ui.bookmarkList.currentRowChanged.connect(self.reloadBookmarkArea)
        self._ui.newBookmark.returnPressed.connect(self.tryAddBookmark)
        self._ui.newBookmark.textChanged.connect(self.reloadBookmarkArea)
        self._ui.addBookmarkButton.clicked.connect(self.tryAddBookmark)
        Utils.setIconViewer(self._ui.addBookmarkButton, Icons.PLUS)
        self._ui.removeBookmarkButton.clicked.connect(self.removeBookmark)
        Utils.setIconViewer(self._ui.removeBookmarkButton, Icons.TRASH)
        self._ui.automaticThemeIcon = Utils.setSvgIcon(self._ui.automaticThemeIcon, Icons.THEME_AUTOMATIC)
        self._ui.automaticThemeRadioButton.setChecked(App.ThemeManager.getThemeMode().isAuto())
        self._ui.automaticThemeRadioButton.toggled.connect(self._updateThemeMode)
        self._ui.lightThemeIcon = Utils.setSvgIcon(self._ui.lightThemeIcon, Icons.THEME_LIGHT)
        self._ui.lightThemeRadioButton.setChecked(App.ThemeManager.getThemeMode().isLight())
        self._ui.lightThemeRadioButton.toggled.connect(self._updateThemeMode)
        self._ui.darkThemeIcon = Utils.setSvgIcon(self._ui.darkThemeIcon, Icons.THEME_DARK)
        self._ui.darkThemeRadioButton.setChecked(App.ThemeManager.getThemeMode().isDark())
        self._ui.darkThemeRadioButton.toggled.connect(self._updateThemeMode)
        self._ui.searchExternalContent.setChecked(App.Preferences.advanced.isSearchExternalContentEnabled())
        self._ui.searchExternalContent.toggled.connect(App.Preferences.advanced.setSearchExternalContentEnabled)
        self._ui.searchExternalContentInfo.clicked.connect(self.showSearchExternalContentInfo)
        Utils.setIconViewer(self._ui.searchExternalContentInfo, Icons.HELP)
        for translationPack in App.Translator.getTranslationPacks():
            self._ui.language.addItem(translationPack.getDisplayName(), userData=translationPack.getId())
        self._ui.language.setCurrentIndex(self._ui.language.findData(App.Translator.getCurrentTranslationPackId()))
        self._ui.language.currentIndexChanged.connect(self.updateLanguage)
        self._ui.timezone.addItems(App.Preferences.localization.getTimezoneNameList())
        self._ui.timezone.setCurrentText(App.Preferences.localization.getTimezone().name())
        self._ui.timezone.currentTextChanged.connect(self.setTimezone)
        self._ui.timezoneInfoIcon = Utils.setSvgIcon(self._ui.timezoneInfoIcon, Icons.ALERT_RED)
        self._ui.downloadSpeed.setRange(DownloadEngineConfig.FILE_DOWNLOAD_MANAGER_MIN_POOL_SIZE, DownloadEngineConfig.FILE_DOWNLOAD_MANAGER_MAX_POOL_SIZE)
        self._ui.downloadSpeed.valueChanged.connect(self.setDownloadSpeed)
        self._ui.speedSpinBox.setRange(DownloadEngineConfig.FILE_DOWNLOAD_MANAGER_MIN_POOL_SIZE, DownloadEngineConfig.FILE_DOWNLOAD_MANAGER_MAX_POOL_SIZE)
        self._ui.speedSpinBox.valueChanged.connect(self.setDownloadSpeed)
        self.setDownloadSpeed(App.FileDownloadManager.getPoolSize())
        self._ui.reconnectEnabled.setChecked(App.Preferences.download.isReconnectEnabled())
        self._ui.reconnectEnabled.toggled.connect(App.Preferences.download.setReconnectEnabled)
        self._ui.reconnectAttemptsSlider.valueChanged.connect(self.setReconnectAttempts)
        self._ui.reconnectAttemptsSpinBox.valueChanged.connect(self.setReconnectAttempts)
        self.setReconnectAttempts(App.Preferences.download.getReconnectAttempts())
        self._ui.reconnectIntervalSlider.valueChanged.connect(self.setReconnectInterval)
        self._ui.reconnectIntervalSpinBox.valueChanged.connect(self.setReconnectInterval)
        self.setReconnectInterval(App.Preferences.download.getReconnectInterval())
        self._ui.updateTrackIntervalSlider.valueChanged.connect(self.setUpdateTrackInterval)
        self._ui.updateTrackIntervalSpinBox.valueChanged.connect(self.setUpdateTrackInterval)
        self.setUpdateTrackInterval(App.Preferences.download.getUpdateTrackInterval())
        self._ui.resetButton.clicked.connect(self.resetSettings)
        self.reloadBookmarkArea()
        App.GlobalDownloadManager.runningCountChangedSignal.connect(self.reload)
        self.reload()
        App.ThemeManager.themeUpdated.connect(self._setupThemeStyle)
        self.retranslateDynamicUi()

    def _setupThemeStyle(self) -> None:
        for index in range(self._ui.bookmarkList.count()):
            self._ui.bookmarkList.item(index).setIcon(Icons.MOVE.icon)

    def reload(self) -> None:
        if App.GlobalDownloadManager.isDownloaderRunning():
            self._ui.languageArea.setEnabled(False)
            self._ui.timezoneArea.setEnabled(False)
            self._ui.resetArea.setEnabled(False)
            self._ui.restrictedLabel.show()
        else:
            self._ui.languageArea.setEnabled(True)
            self._ui.timezoneArea.setEnabled(True)
            self._ui.resetArea.setEnabled(True)
            self._ui.restrictedLabel.hide()

    def windowCloseChanged(self, index: int) -> None:
        App.Preferences.general.setSystemTrayEnabled(False if index == 0 else True)

    def setStreamFilename(self) -> None:
        App.Preferences.templates.setStreamFilename(self._ui.streamFilename.text())

    def setVideoFilename(self) -> None:
        App.Preferences.templates.setVideoFilename(self._ui.videoFilename.text())

    def setClipFilename(self) -> None:
        App.Preferences.templates.setClipFilename(self._ui.clipFilename.text())

    def reloadBookmarkArea(self) -> None:
        selected = self._ui.bookmarkList.currentRow() != -1
        text = self._ui.newBookmark.text().strip().lower()
        textNotEmptyOrDuplicate = text != "" and len(self._ui.bookmarkList.findItems(text, QtCore.Qt.MatchFlag.MatchFixedString)) == 0
        self._ui.addBookmarkButton.setEnabled(textNotEmptyOrDuplicate)
        self._ui.removeBookmarkButton.setEnabled(selected)

    def tryAddBookmark(self) -> None:
        if self._ui.addBookmarkButton.isEnabled():
            self.addBookmark(self._ui.newBookmark.text().strip().lower())
            self._ui.newBookmark.clear()

    def addBookmark(self, bookmark: str) -> None:
        item = QtWidgets.QListWidgetItem(bookmark)
        item.setIcon(Icons.MOVE.icon)
        item.setToolTip(T("messages.#drag_change_order"))
        self._ui.bookmarkList.addItem(item)
        self._ui.newBookmark.clear()

    def removeBookmark(self) -> None:
        self._ui.bookmarkList.takeItem(self._ui.bookmarkList.currentRow())
        self._ui.bookmarkList.setCurrentRow(-1)

    def saveBookmark(self) -> None:
        App.Preferences.general.setBookmarks([self._ui.bookmarkList.item(index).text() for index in range(self._ui.bookmarkList.count())])

    def _updateThemeMode(self) -> None:
        if self._ui.automaticThemeRadioButton.isChecked():
            App.ThemeManager.setThemeMode(App.ThemeManager.Modes.AUTO)
        elif self._ui.lightThemeRadioButton.isChecked():
            App.ThemeManager.setThemeMode(App.ThemeManager.Modes.LIGHT)
        elif self._ui.darkThemeRadioButton.isChecked():
            App.ThemeManager.setThemeMode(App.ThemeManager.Modes.DARK)

    def showSearchExternalContentInfo(self) -> None:
        Utils.info("information", "messages.#allow_url_search_retrieve_external_cont", parent=self)

    def updateLanguage(self) -> None:
        App.Translator.setTranslationPack(self._ui.language.currentData())

    def setTimezone(self, timezone: str) -> None:
        App.Preferences.localization.setTimezone(bytes(timezone, encoding="utf-8"))
        self.requestRestart()

    def setDownloadSpeed(self, speed: int) -> None:
        App.FileDownloadManager.setPoolSize(speed)
        self._ui.downloadSpeed.setValueSilent(speed)
        self._ui.speedSpinBox.setValueSilent(speed)

    def setReconnectAttempts(self, attempts: int) -> None:
        App.Preferences.download.setReconnectAttempts(attempts)
        self._ui.reconnectAttemptsSlider.setValueSilent(attempts)
        self._ui.reconnectAttemptsSpinBox.setValueSilent(attempts)

    def setReconnectInterval(self, interval: int) -> None:
        App.Preferences.download.setReconnectInterval(interval)
        self._ui.reconnectIntervalSlider.setValueSilent(interval)
        self._ui.reconnectIntervalSpinBox.setValueSilent(interval)

    def setUpdateTrackInterval(self, interval: int) -> None:
        App.Preferences.download.setUpdateTrackInterval(interval)
        self._ui.updateTrackIntervalSlider.setValueSilent(interval)
        self._ui.updateTrackIntervalSpinBox.setValueSilent(interval)

    def resetSettings(self) -> None:
        if Utils.ask("warning", "prompts.#this_will_reset_all_settings_proceed", parent=self):
            App.Preferences.reset()
            self.requestRestart()

    def askDefaultDirectory(self) -> None:
        directory = Utils.askDirectory(self._ui.defaultDirectory.text() or Config.DEFAULT_DIRECTORY, parent=self)
        if directory != "":
            App.Preferences.general.setDefaultDirectory(directory)
            self._ui.defaultDirectory.setText(directory)

    def setDefaultDirectoryFromLineEdit(self) -> None:
        directory = self._ui.defaultDirectory.text().strip()
        directory = directory.strip("\"'")
        App.Preferences.general.setDefaultDirectory(directory)
        self._ui.defaultDirectory.setText(directory)

    def requestRestart(self) -> None:
        self.restartRequired.emit()

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self._ui.retranslateUi(self)
            self.retranslateDynamicUi()

    def retranslateDynamicUi(self) -> None:
        self._ui.defaultDirectoryLabel.setText(T("messages.default_directory"))
        self._ui.searchDefaultDirectory.setToolTip(T("messages.browse"))
        self._ui.reconnectArea.setTitle(T("messages.network_reconnection"))
        self._ui.reconnectEnabled.setText(T("messages.enable_reconnect"))
        self._ui.reconnectAttemptsLabel.setText(T("messages.reconnect_attempts"))
        self._ui.reconnectIntervalLabel.setText(T("messages.retry_interval_ms"))
        self._ui.updateTrackIntervalLabel.setText(T("messages.update_track_interval_ms"))
