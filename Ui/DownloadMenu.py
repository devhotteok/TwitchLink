from Core.Ui import *
from Download.DownloadInfo import DownloadInfo
from Services.FileNameLocker import FileNameLocker
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator


class DownloadMenu(QtWidgets.QDialog, WindowGeometryManager):
    downloadRequested = QtCore.pyqtSignal(DownloadInfo)

    def __init__(self, downloadInfo: DownloadInfo, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("downloadMenu", self)
        self.finished.connect(self.saveWindowGeometry)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowMaximizeButtonHint)
        self.downloadInfo = downloadInfo
        self.setWindowGeometryKey(f"{self.getWindowGeometryKey()}/{self.downloadInfo.type.toString()}")
        self.loadWindowGeometry()
        self._ui.videoWidget = Utils.setPlaceholder(self._ui.videoWidget, Ui.VideoWidget(self.downloadInfo.content, parent=self))
        self._ui.cropSettingsInfoIcon = Utils.setSvgIcon(self._ui.cropSettingsInfoIcon, Icons.INFO)
        self._ui.cropRangeInfoIcon = Utils.setSvgIcon(self._ui.cropRangeInfoIcon, Icons.ALERT_RED)
        self.loadOptions()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            event.ignore()
        else:
            super().keyPressEvent(event)

    def loadOptions(self) -> None:
        self._ui.windowTitleLabel.setText(T("messages.#download", type=T(self.downloadInfo.type.toString())))
        self.reloadFileDirectory()
        self._ui.createSubfolderForDownloadsCheckBox.setChecked(self.downloadInfo.isCreateSubfolderForDownloadsEnabled())
        self._ui.createSubfolderForDownloadsCheckBox.toggled.connect(self.downloadInfo.setCreateSubfolderForDownloadsEnabled)
        self._ui.createSubfolderForDownloadsCheckBox.toggled.connect(lambda: self.reloadFileDirectory())
        self._ui.fileFormat.currentTextChanged.connect(self.setFormat)
        self._ui.searchDirectory.clicked.connect(self.askSaveAs)
        for resolution in self.downloadInfo.playback.getResolutions():
            self._ui.resolution.addItem(FileNameGenerator.generateResolutionName(resolution))
        self._ui.resolution.setCurrentIndex(self.downloadInfo.selectedResolutionIndex)
        self._ui.resolution.currentIndexChanged.connect(self.setResolution)
        self.setupChatArea()
        if self.downloadInfo.type.isStream():
            self._ui.cropArea.hide()
            if self.downloadInfo.playback.token.hideAds:
                self._ui.adBlockArea.hide()
            else:
                self.setupAdBlockArea()
            self.setupEncoderArea()
            self._ui.advancedArea.hide()
        elif self.downloadInfo.type.isVideo():
            self.setupCropArea()
            self._ui.adBlockArea.hide()
            self.setupEncoderArea()
            self._ui.unmuteVideoCheckBox.setChecked(self.downloadInfo.isUnmuteVideoEnabled())
            self._ui.unmuteVideoCheckBox.toggled.connect(self.downloadInfo.setUnmuteVideoEnabled)
            self._ui.unmuteVideoInfo.clicked.connect(self.showUnmuteVideoInfo)
            Utils.setIconViewer(self._ui.unmuteVideoInfo, Icons.HELP)
            self._ui.updateTrackCheckBox.setChecked(self.downloadInfo.isUpdateTrackEnabled())
            self._ui.updateTrackCheckBox.toggled.connect(self.setUpdateTrackEnabled)
            self._ui.updateTrackInfo.clicked.connect(self.showUpdateTrackInfo)
            Utils.setIconViewer(self._ui.updateTrackInfo, Icons.HELP)
            self._ui.prioritizeCheckBox.setChecked(self.downloadInfo.isPrioritizeEnabled())
            self._ui.prioritizeCheckBox.toggled.connect(self.downloadInfo.setPrioritizeEnabled)
            self._ui.prioritizeInfo.clicked.connect(self.showPrioritizeInfo)
            Utils.setIconViewer(self._ui.prioritizeInfo, Icons.HELP)
            self.reloadCropArea()
        else:
            self._ui.cropArea.hide()
            self._ui.adBlockArea.hide()
            self._ui.encoderArea.hide()
            self._ui.unmuteVideoArea.hide()
            self._ui.updateTrackArea.hide()
            self._ui.prioritizeCheckBox.setChecked(self.downloadInfo.isPrioritizeEnabled())
            self._ui.prioritizeCheckBox.toggled.connect(self.downloadInfo.setPrioritizeEnabled)
            self._ui.prioritizeInfo.clicked.connect(self.showPrioritizeInfo)
            Utils.setIconViewer(self._ui.prioritizeInfo, Icons.HELP)

    def reloadFileDirectory(self) -> None:
        self._ui.currentDirectory.setText(self.downloadInfo.getAbsoluteFileName())
        self._ui.currentDirectory.setToolTip(self.downloadInfo.getAbsoluteFileName())
        self._ui.fileFormat.blockSignals(True)
        self._ui.fileFormat.clear()
        self._ui.fileFormat.addItems(self.downloadInfo.getAvailableFormats())
        self._ui.fileFormat.setCurrentText(self.downloadInfo.fileFormat)
        self._ui.fileFormat.blockSignals(False)

    def setFormat(self, format: str) -> None:
        self.downloadInfo.setFileFormat(format)
        self.reloadFileDirectory()

    def setResolution(self, index: int) -> None:
        self.downloadInfo.setResolution(index)
        self.reloadFileDirectory()
        if self.hasResolutionInFileNameTemplate():
            if Utils.ask("filename-change", "prompts.#the_filename_template_contains_'resolut", defaultOk=True, parent=self):
                self.downloadInfo.setFileName(self.downloadInfo.generateFileName())
                self.reloadFileDirectory()

    def hasResolutionInFileNameTemplate(self) -> bool:
        if self.downloadInfo.type.isStream():
            fileNameTemplate = FileNameGenerator.getStreamFileNameTemplate()
        elif self.downloadInfo.type.isVideo():
            fileNameTemplate = FileNameGenerator.getVideoFileNameTemplate()
        else:
            fileNameTemplate = FileNameGenerator.getClipFileNameTemplate()
        return "{resolution}" in fileNameTemplate

    def setupCropArea(self) -> None:
        self._ui.cropArea.setTitle(f"{T('crop')} / {T("messages.#total_length", duration=self.downloadInfo.content.durationString)}")
        self._ui.cropFromStartRadioButton.toggled.connect(self.reloadCropArea)
        self._ui.cropToEndRadioButton.toggled.connect(self.checkUpdateTrack)
        self._ui.fromSpinH.valueChanged.connect(self.startRangeChanged)
        self._ui.fromSpinM.valueChanged.connect(self.startRangeChanged)
        self._ui.fromSpinS.valueChanged.connect(self.startRangeChanged)
        self._ui.toSpinH.valueChanged.connect(self.endRangeChanged)
        self._ui.toSpinM.valueChanged.connect(self.endRangeChanged)
        self._ui.toSpinS.valueChanged.connect(self.endRangeChanged)
        self._ui.cropSettingsInfoButton.clicked.connect(self.showCropInfo)
        Utils.setIconViewer(self._ui.cropSettingsInfoButton, Icons.HELP)
        startMilliseconds, endMilliseconds = self.downloadInfo.getCropRangeMilliseconds()
        if startMilliseconds != None:
            self._ui.cropFromSelectRadioButton.setChecked(True)
            self.setFromSeconds(int(startMilliseconds / 1000))
        if endMilliseconds != None:
            self._ui.cropToSelectRadioButton.setChecked(True)
            self.setToSeconds(int(endMilliseconds / 1000))

    def setupAdBlockArea(self) -> None:
        self._ui.adBlockSkipSegmentsRadioButton.setChecked(self.downloadInfo.isSkipAdsEnabled())
        self._ui.adBlockAlternativeScreenRadioButton.setChecked(not self.downloadInfo.isSkipAdsEnabled())
        self._ui.adBlockSkipSegmentsRadioButton.toggled.connect(self.downloadInfo.setSkipAdsEnabled)
        self._ui.adBlockInfo.clicked.connect(self.showAdBlockInfo)
        Utils.setIconViewer(self._ui.adBlockInfo, Icons.HELP)

    def setupEncoderArea(self) -> None:
        self._ui.remuxRadioButton.setChecked(self.downloadInfo.isRemuxEnabled())
        self._ui.concatRadioButton.setChecked(not self.downloadInfo.isRemuxEnabled())
        self._ui.remuxRadioButton.toggled.connect(self.downloadInfo.setRemuxEnabled)
        self._ui.encoderInfo.clicked.connect(self.showEncoderInfo)
        Utils.setIconViewer(self._ui.encoderInfo, Icons.HELP)

    def setupChatArea(self) -> None:
        self._ui.downloadChatCheckBox.setChecked(self.downloadInfo.downloadChat)
        self._ui.downloadChatCheckBox.toggled.connect(self.downloadInfo.optionHistory.setDownloadChatEnabled)
        self._ui.downloadChatCheckBox.toggled.connect(lambda enabled: setattr(self.downloadInfo, 'downloadChat', enabled))
        self._ui.downloadChatCheckBox.toggled.connect(self.onDownloadChatToggled)
        self._ui.downloadChatInfo.clicked.connect(self.showDownloadChatInfo)
        Utils.setIconViewer(self._ui.downloadChatInfo, Icons.HELP)

    def onDownloadChatToggled(self, enabled: bool) -> None:
        from Core import App
        if enabled:
            if App.Preferences.download.isCreateSubfolderForDownloadsEnabled():
                self._ui.createSubfolderForDownloadsCheckBox.setChecked(True)
        else:
            self._ui.createSubfolderForDownloadsCheckBox.setChecked(False)

    def startRangeChanged(self) -> None:
        self.setFromSeconds(self.checkCropRange(self.getFromSeconds(), maximum=int(self.downloadInfo.content.lengthSeconds) - 1))

    def endRangeChanged(self) -> None:
        self.setToSeconds(self.checkCropRange(self.getToSeconds(), minimum=1))

    def isCropRangeInvalid(self) -> bool:
        return self.getFromSeconds() >= self.getToSeconds()

    def validateCropRange(self) -> None:
        invalid = self.isCropRangeInvalid()
        styleSheet = "QSpinBox, QLabel {color: red;}" if invalid else ""
        self._ui.fromTimeBar.setStyleSheet(styleSheet)
        self._ui.toTimeBar.setStyleSheet(styleSheet)
        self.reloadCropInfoArea()
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(not invalid)

    def getFromSeconds(self) -> int:
        return self._ui.fromSpinH.value() * 3600 + self._ui.fromSpinM.value() * 60 + self._ui.fromSpinS.value()

    def getToSeconds(self) -> int:
        return self._ui.toSpinH.value() * 3600 + self._ui.toSpinM.value() * 60 + self._ui.toSpinS.value()

    def setFromSeconds(self, seconds: int) -> None:
        self._ui.fromSpinH.setValueSilent(seconds // 3600)
        self._ui.fromSpinM.setValueSilent(seconds % 3600 // 60)
        self._ui.fromSpinS.setValueSilent(seconds % 3600 % 60)
        self.validateCropRange()

    def setToSeconds(self, seconds: int) -> None:
        self._ui.toSpinH.setValueSilent(seconds // 3600)
        self._ui.toSpinM.setValueSilent(seconds % 3600 // 60)
        self._ui.toSpinS.setValueSilent(seconds % 3600 % 60)
        self.validateCropRange()

    def checkCropRange(self, seconds: int, maximum: int | None = None, minimum: int | None = None) -> int:
        if maximum == None:
            maximum = int(self.downloadInfo.content.lengthSeconds)
        if minimum == None:
            minimum = 0
        if seconds > maximum:
            return maximum
        elif seconds < minimum:
            return minimum
        else:
            return seconds

    def reloadCropArea(self) -> None:
        self._ui.fromTimeBar.setEnabled(not self._ui.cropFromStartRadioButton.isChecked())
        self._ui.toTimeBar.setEnabled(not self._ui.cropToEndRadioButton.isChecked())
        if self._ui.cropFromStartRadioButton.isChecked():
            self.setFromSeconds(0)
        if self._ui.cropToEndRadioButton.isChecked():
            self.setToSeconds(int(self.downloadInfo.content.lengthSeconds))
        self.reloadCropInfoArea()

    def reloadCropInfoArea(self) -> None:
        hasCropRange = self._ui.cropFromSelectRadioButton.isChecked() or self._ui.cropToSelectRadioButton.isChecked()
        showRangeInfo = self.isCropRangeInvalid()
        self._ui.cropInfoArea.setCurrentIndex(1 if showRangeInfo else 0)
        self._ui.cropInfoArea.setVisible(showRangeInfo or hasCropRange)

    def checkUpdateTrack(self) -> None:
        self.reloadCropArea()
        if self._ui.updateTrackCheckBox.isChecked() and not self._ui.cropToEndRadioButton.isChecked():
            if Utils.ask("warning", "prompts.#update_track_mode_is_currently_enabled", defaultOk=True, parent=self):
                self._ui.updateTrackCheckBox.setCheckState(QtCore.Qt.CheckState.Unchecked)
            else:
                self._ui.cropToEndRadioButton.setChecked(True)

    def showCropInfo(self) -> None:
        Utils.info(
            "information",
            T("messages.#for_precise_range_handling_it_is_necess", appName=Config.APP_NAME),
            contentTranslate=False,
            parent=self
        )

    def askSaveAs(self) -> None:
        directory = self.downloadInfo.getAbsoluteFileName()
        filters = self.downloadInfo.getAvailableFormats()
        initialFilter = self.downloadInfo.fileFormat
        newDirectory = Utils.askSaveAs(directory, filters, initialFilter, parent=self)
        if newDirectory != None:
            self._ui.createSubfolderForDownloadsCheckBox.setChecked(False)
            self.downloadInfo.setAbsoluteFileName(newDirectory)
            self.reloadFileDirectory()

    def showAdBlockInfo(self) -> None:
        skipSegmentsInfo = T("info.#_skip_segments_ads_are_skipped_but_stre")
        alternativeScreenInfo = T("info.#_alternative_screen_displays_alternate")
        Utils.info("information", f"{T("info.#if_commercials_are_broadcast_during_thi")}\n\n{skipSegmentsInfo}\n\n\n{alternativeScreenInfo}", contentTranslate=False, parent=self)

    def showEncoderInfo(self) -> None:
        remuxInfo = T("prompts.#_remux_file_will_be_saved_as_standard_v")
        concatInfo = T("errors.#_concat_this_feature_enables_you_store")
        Utils.info("information", f"{remuxInfo}\n\n\n{concatInfo}", contentTranslate=False, parent=self)

    def showUnmuteVideoInfo(self) -> None:
        Utils.info("information", "errors.#if_there_are_no_problems_sound_source_u", parent=self)

    def showDownloadChatInfo(self) -> None:
        Utils.info("information", "messages.#the_chat_will_be_downloaded_in_json", parent=self)

    def showUpdateTrackInfo(self) -> None:
        Utils.info("information", "messages.#downloads_live_replay_continuously_unti", parent=self)

    def showPrioritizeInfo(self) -> None:
        Utils.info("information", "messages.#this_download_will_be_prioritized_downl", parent=self)

    def setUpdateTrackEnabled(self, enabled: bool) -> None:
        self.downloadInfo.setUpdateTrackEnabled(enabled)
        if self._ui.updateTrackCheckBox.isChecked() and not self._ui.cropToEndRadioButton.isChecked():
            if Utils.ask("warning", "prompts.#the_end_crop_range_is_currently_set_ena", defaultOk=True, parent=self):
                self._ui.cropToEndRadioButton.setChecked(True)
            else:
                self._ui.updateTrackCheckBox.setCheckState(QtCore.Qt.CheckState.Unchecked)

    def saveCropRange(self) -> None:
        self.downloadInfo.setCropRangeMilliseconds(
            None if self._ui.cropFromStartRadioButton.isChecked() else self.getFromSeconds() * 1000,
            None if self._ui.cropToEndRadioButton.isChecked() else self.getToSeconds() * 1000
        )

    def checkDownloadAvailable(self) -> bool:
        if not FileNameLocker.isAvailable(self.downloadInfo.getAbsoluteFileName()):
            Utils.info("error", "messages.#there_is_another_download_progress_same", parent=self)
            return False
        elif Utils.isFile(self.downloadInfo.getAbsoluteFileName()):
            if not Utils.ask("overwrite", "prompts.#a_file_same_name_already_exists_overwri", parent=self):
                return False
        elif not Utils.isDirectory(self.downloadInfo.directory) or Utils.isDirectory(self.downloadInfo.getAbsoluteFileName()):
            Utils.info("error", "errors.#the_target_directory_or_filename_is_una", parent=self)
            return False
        return True

    def accept(self) -> None:
        if self.checkDownloadAvailable():
            if self.downloadInfo.type.isVideo():
                self.saveCropRange()
            self.downloadInfo.saveOptionHistory()
            self.downloadRequested.emit(self.downloadInfo)
            super().accept()
        else:
            self.askSaveAs()

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self._ui.retranslateUi(self)
            self.retranslateDynamicUi()

    def retranslateDynamicUi(self) -> None:
        pass
