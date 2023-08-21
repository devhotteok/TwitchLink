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
        self._ui.cropSettingsInfoIcon = Utils.setSvgIcon(self._ui.cropSettingsInfoIcon, Icons.INFO_ICON)
        self._ui.cropRangeInfoIcon = Utils.setSvgIcon(self._ui.cropRangeInfoIcon, Icons.ALERT_RED_ICON)
        self.loadOptions()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() in (QtCore.Qt.Key.Key_Return, QtCore.Qt.Key.Key_Enter):
            event.ignore()
        else:
            super().keyPressEvent(event)

    def loadOptions(self) -> None:
        self._ui.windowTitleLabel.setText(T("#Download {type}", type=T(self.downloadInfo.type.toString())))
        self.reloadFileDirectory()
        self._ui.fileFormat.currentTextChanged.connect(self.setFormat)
        self._ui.searchDirectory.clicked.connect(self.askSaveAs)
        for resolution in self.downloadInfo.playback.getResolutions():
            self._ui.resolution.addItem(FileNameGenerator.generateResolutionName(resolution))
        self._ui.resolution.setCurrentIndex(self.downloadInfo.selectedResolutionIndex)
        self._ui.resolution.currentIndexChanged.connect(self.setResolution)
        if self.downloadInfo.type.isStream():
            self._ui.cropArea.hide()
            self._ui.remuxRadioButton.setChecked(self.downloadInfo.isRemuxEnabled())
            self._ui.concatRadioButton.setChecked(not self.downloadInfo.isRemuxEnabled())
            self._ui.remuxRadioButton.toggled.connect(self.downloadInfo.setRemuxEnabled)
            self._ui.encoderInfo.clicked.connect(self.showEncoderInfo)
            self._ui.advancedArea.hide()
        elif self.downloadInfo.type.isVideo():
            self.setupCropArea()
            self._ui.remuxRadioButton.setChecked(self.downloadInfo.isRemuxEnabled())
            self._ui.concatRadioButton.setChecked(not self.downloadInfo.isRemuxEnabled())
            self._ui.remuxRadioButton.toggled.connect(self.downloadInfo.setRemuxEnabled)
            self._ui.encoderInfo.clicked.connect(self.showEncoderInfo)
            self._ui.unmuteVideoCheckBox.setChecked(self.downloadInfo.isUnmuteVideoEnabled())
            self._ui.unmuteVideoCheckBox.toggled.connect(self.downloadInfo.setUnmuteVideoEnabled)
            self._ui.unmuteVideoInfo.clicked.connect(self.showUnmuteVideoInfo)
            self._ui.updateTrackCheckBox.setChecked(self.downloadInfo.isUpdateTrackEnabled())
            self._ui.updateTrackCheckBox.toggled.connect(self.setUpdateTrackEnabled)
            self._ui.updateTrackInfo.clicked.connect(self.showUpdateTrackInfo)
            self._ui.prioritizeCheckBox.setChecked(self.downloadInfo.isPrioritizeEnabled())
            self._ui.prioritizeCheckBox.toggled.connect(self.downloadInfo.setPrioritizeEnabled)
            self._ui.prioritizeInfo.clicked.connect(self.showPrioritizeInfo)
            self.reloadCropArea()
        else:
            self._ui.cropArea.hide()
            self._ui.encoderArea.hide()
            self._ui.unmuteVideoArea.hide()
            self._ui.updateTrackArea.hide()
            self._ui.prioritizeCheckBox.setChecked(self.downloadInfo.isPrioritizeEnabled())
            self._ui.prioritizeCheckBox.toggled.connect(self.downloadInfo.setPrioritizeEnabled)
            self._ui.prioritizeInfo.clicked.connect(self.showPrioritizeInfo)

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
            if Utils.ask("filename-change", "#The filename template contains a 'resolution' variable. Do you want to create a new filename based on the changed resolution?", defaultOk=True, parent=self):
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
        self._ui.cropArea.setTitle(f"{T('crop')} / {T('#Total Length: {duration}', duration=self.downloadInfo.content.durationString)}")
        self._ui.cropFromStartRadioButton.toggled.connect(self.reloadCropArea)
        self._ui.cropToEndRadioButton.toggled.connect(self.checkUpdateTrack)
        self._ui.fromSpinH.valueChanged.connect(self.startRangeChanged)
        self._ui.fromSpinM.valueChanged.connect(self.startRangeChanged)
        self._ui.fromSpinS.valueChanged.connect(self.startRangeChanged)
        self._ui.toSpinH.valueChanged.connect(self.endRangeChanged)
        self._ui.toSpinM.valueChanged.connect(self.endRangeChanged)
        self._ui.toSpinS.valueChanged.connect(self.endRangeChanged)
        self._ui.cropSettingsInfoButton.clicked.connect(self.showCropInfo)
        startMilliseconds, endMilliseconds = self.downloadInfo.getCropRangeMilliseconds()
        if startMilliseconds != None:
            self._ui.cropFromSelectRadioButton.setChecked(True)
            self.setFromSeconds(int(startMilliseconds / 1000))
        if endMilliseconds != None:
            self._ui.cropToSelectRadioButton.setChecked(True)
            self.setToSeconds(int(endMilliseconds / 1000))

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
            if Utils.ask("warning", "#Update track mode is currently enabled.\nSetting the end of the crop range will not track updates.\nProceed?", defaultOk=True, parent=self):
                self._ui.updateTrackCheckBox.setCheckState(QtCore.Qt.CheckState.Unchecked)
            else:
                self._ui.cropToEndRadioButton.setChecked(True)

    def showCropInfo(self) -> None:
        Utils.info(
            "information",
            T("#For precise range handling, it is necessary to re-encode the video from the beginning, a process which can be very time-consuming.\nTo speed up this process, {appName} performs the cutting operation using computationally inexpensive points near the specified range, without re-encoding.\nThere is no loss during this process, but a few additional seconds may be saved before and after the specified range.\nIf precise range handling is required, please process the downloaded video using a professional video editor.", appName=Config.APP_NAME),
            contentTranslate=False,
            parent=self
        )

    def askSaveAs(self) -> None:
        directory = self.downloadInfo.getAbsoluteFileName()
        filters = self.downloadInfo.getAvailableFormats()
        initialFilter = self.downloadInfo.fileFormat
        newDirectory = Utils.askSaveAs(directory, filters, initialFilter, parent=self)
        if newDirectory != None:
            self.downloadInfo.setAbsoluteFileName(newDirectory)
            self.reloadFileDirectory()

    def showEncoderInfo(self) -> None:
        remuxInfo = T("#[Remux]\n\nThe file will be saved as a standard video file.\nThis involves a minor conversion process of the Transport Stream file to ensure its compatibility with standard players.\nThe quality of the video is retained, with only additional information about the video being modified for compatibility with standard players.")
        concatInfo = T("#[Concat]\n\nThis feature enables you to store Transport Stream file in its original form, without any conversion to ensure its compatibility with standard players.\nSince these files are typically designed for streaming, they may not play correctly on certain players.\nAdditionally, if commercials are broadcast during a live stream or parts are missing due to network issues, some players might not display the entire length of the video correctly.")
        Utils.info("information", f"{remuxInfo}\n\n\n{concatInfo}", contentTranslate=False, parent=self)

    def showUnmuteVideoInfo(self) -> None:
        Utils.info("information", "#If there are no problems with the sound source used, or if there are parts that have been muted in error despite having permission to use them, you can use this function to unmute them.\nIn some cases, unmute may not be successful.", parent=self)

    def showUpdateTrackInfo(self) -> None:
        Utils.info("information", "#Downloads the live replay continuously until the broadcast ends.\nThe download ends if there are no changes in the video for a certain amount of time.", parent=self)

    def showPrioritizeInfo(self) -> None:
        Utils.info("information", "#This download will be prioritized. Downloads with this option take precedence over those without.", parent=self)

    def setUpdateTrackEnabled(self, enabled: bool) -> None:
        self.downloadInfo.setUpdateTrackEnabled(enabled)
        if self._ui.updateTrackCheckBox.isChecked() and not self._ui.cropToEndRadioButton.isChecked():
            if Utils.ask("warning", "#The end of the crop range is currently set.\nEnabling update track mode will ignore the end of the crop range and continue downloading.\nProceed?", defaultOk=True, parent=self):
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
            Utils.info("error", "#There is another download in progress with the same file name.", parent=self)
            return False
        elif Utils.isFile(self.downloadInfo.getAbsoluteFileName()):
            if not Utils.ask("overwrite", "#A file with the same name already exists.\nOverwrite?", parent=self):
                return False
        elif not Utils.isDirectory(self.downloadInfo.directory) or Utils.isDirectory(self.downloadInfo.getAbsoluteFileName()):
            Utils.info("error", "#The target directory or filename is unavailable.", parent=self)
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