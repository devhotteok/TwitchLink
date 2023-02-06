from Core.Ui import *
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator
from Ui.Components.Utils.ResolutionNameGenerator import ResolutionNameGenerator
from Ui.Components.Utils.DownloadChecker import DownloadChecker


class DownloadMenu(QtWidgets.QDialog, UiFile.downloadMenu, WindowGeometryManager):
    def __init__(self, downloadInfo, parent=None):
        super(DownloadMenu, self).__init__(parent=parent)
        self.finished.connect(self.saveWindowGeometry)
        self.ignoreKey(QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter)
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint)
        self.downloadInfo = downloadInfo
        self.setWindowGeometryKey(f"{self.getWindowGeometryKey()}/{self.downloadInfo.type.toString()}")
        self.loadWindowGeometry()
        self.videoWidget = Utils.setPlaceholder(self.videoWidget, Ui.VideoWidget(self.downloadInfo.videoData, viewOnly=False, parent=self))
        self.cropSettingsInfoIcon = Utils.setSvgIcon(self.cropSettingsInfoIcon, Icons.INFO_ICON)
        self.cropRangeInfoIcon = Utils.setSvgIcon(self.cropRangeInfoIcon, Icons.ALERT_RED_ICON)
        self.loadOptions()

    def loadOptions(self):
        self.windowTitleLabel.setText(T("#Download {type}", type=T(self.downloadInfo.type.toString())))
        self.reloadFileDirectory()
        self.fileFormat.currentTextChanged.connect(self.setFormat)
        self.searchDirectory.clicked.connect(self.askSaveAs)
        for resolution in self.downloadInfo.accessToken.getResolutions():
            self.resolution.addItem(ResolutionNameGenerator.generateResolutionName(resolution))
        self.resolution.setCurrentIndex(self.downloadInfo.selectedResolutionIndex)
        self.resolution.currentIndexChanged.connect(self.setResolution)
        if self.downloadInfo.type.isStream():
            self.cropArea.hide()
            self.advancedArea.hide()
        elif self.downloadInfo.type.isVideo():
            self.setupCropArea()
            self.unmuteVideoCheckBox.setChecked(self.downloadInfo.isUnmuteVideoEnabled())
            self.unmuteVideoCheckBox.toggled.connect(self.downloadInfo.setUnmuteVideoEnabled)
            self.unmuteVideoInfo.clicked.connect(self.showUnmuteVideoInfo)
            self.updateTrackCheckBox.setChecked(self.downloadInfo.isUpdateTrackEnabled())
            self.updateTrackCheckBox.toggled.connect(self.setUpdateTrack)
            self.updateTrackInfo.clicked.connect(self.showUpdateTrackInfo)
            self.prioritizeCheckBox.setChecked(self.downloadInfo.isPrioritizeEnabled())
            self.prioritizeCheckBox.toggled.connect(self.downloadInfo.setPrioritizeEnabled)
            self.prioritizeInfo.clicked.connect(self.showPrioritizeInfo)
            self.reloadCropArea()
        else:
            self.cropArea.hide()
            self.unmuteVideoArea.hide()
            self.updateTrackArea.hide()
            self.prioritizeCheckBox.setChecked(self.downloadInfo.isPrioritizeEnabled())
            self.prioritizeCheckBox.toggled.connect(self.downloadInfo.setPrioritizeEnabled)
            self.prioritizeInfo.clicked.connect(self.showPrioritizeInfo)

    def reloadFileDirectory(self):
        self.currentDirectory.setText(self.downloadInfo.getAbsoluteFileName())
        self.currentDirectory.setToolTip(self.downloadInfo.getAbsoluteFileName())
        self.fileFormat.blockSignals(True)
        self.fileFormat.clear()
        self.fileFormat.addItems(self.downloadInfo.getAvailableFormats())
        self.fileFormat.setCurrentText(self.downloadInfo.fileFormat)
        self.fileFormat.blockSignals(False)

    def setFormat(self, fileFormat):
        self.downloadInfo.setFileFormat(fileFormat)
        self.reloadFileDirectory()

    def setResolution(self, index):
        self.downloadInfo.setResolution(index)
        self.reloadFileDirectory()
        if self.hasResolutionInFileNameTemplate():
            if self.ask("filename-change", "#The filename template contains a 'resolution' variable. Do you want to create a new filename based on the changed resolution?", defaultOk=True):
                self.downloadInfo.setFileName(self.downloadInfo.generateFileName())
                self.reloadFileDirectory()

    def hasResolutionInFileNameTemplate(self):
        if self.downloadInfo.type.isStream():
            fileNameTemplate = FileNameGenerator.getStreamFileNameTemplate()
        elif self.downloadInfo.type.isVideo():
            fileNameTemplate = FileNameGenerator.getVideoFileNameTemplate()
        else:
            fileNameTemplate = FileNameGenerator.getClipFileNameTemplate()
        return "{resolution}" in fileNameTemplate

    def setupCropArea(self):
        self.cropArea.setTitle(f"{T('crop')} / {T('#Total Length: {duration}', duration=self.downloadInfo.videoData.durationString)}")
        self.cropFromStartRadioButton.toggled.connect(self.reloadCropArea)
        self.cropToEndRadioButton.toggled.connect(self.checkUpdateTrack)
        self.fromSpinH.valueChanged.connect(self.startRangeChanged)
        self.fromSpinM.valueChanged.connect(self.startRangeChanged)
        self.fromSpinS.valueChanged.connect(self.startRangeChanged)
        self.toSpinH.valueChanged.connect(self.endRangeChanged)
        self.toSpinM.valueChanged.connect(self.endRangeChanged)
        self.toSpinS.valueChanged.connect(self.endRangeChanged)
        self.cropSettingsInfoButton.clicked.connect(self.showCropInfo)
        h, m, s = Utils.toTime(self.downloadInfo.videoData.lengthSeconds)
        self.fromSpinH.setMaximum(h + 1)
        self.toSpinH.setMaximum(h + 1)
        range = self.downloadInfo.getRangeInSeconds()
        if range[0] != None:
            self.cropFromSelectRadioButton.setChecked(True)
            self.setFromSpin(*Utils.toTime(range[0]))
        if range[1] != None:
            self.cropToSelectRadioButton.setChecked(True)
            self.setToSpin(*Utils.toTime(range[1]))
        self.clippingModeCheckBox.setChecked(self.downloadInfo.isClippingModeEnabled())
        self.clippingModeCheckBox.toggled.connect(self.setClippingMode)
        self.clippingModeInfo.clicked.connect(self.showClippingModeInfo)

    def startRangeChanged(self):
        self.setFromSpin(*self.checkCropRange(*self.getFromSpin(), maximum=self.downloadInfo.videoData.lengthSeconds - 1))

    def endRangeChanged(self):
        self.setToSpin(*self.checkCropRange(*self.getToSpin(), minimum=1))

    def isCropRangeInvalid(self):
        fromSpinSeconds = Utils.toSeconds(*self.getFromSpin())
        toSpinSeconds = Utils.toSeconds(*self.getToSpin())
        return fromSpinSeconds >= toSpinSeconds

    def validateCropRange(self):
        invalid = self.isCropRangeInvalid()
        styleSheet = "QSpinBox, QLabel {color: red;}" if invalid else ""
        self.fromTimeBar.setStyleSheet(styleSheet)
        self.toTimeBar.setStyleSheet(styleSheet)
        self.reloadCropInfoArea()
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(not invalid)

    def getFromSpin(self):
        return self.fromSpinH.value(), self.fromSpinM.value(), self.fromSpinS.value()

    def getToSpin(self):
        return self.toSpinH.value(), self.toSpinM.value(), self.toSpinS.value()

    def setFromSpin(self, h, m, s):
        self.fromSpinH.setValueSilent(h)
        self.fromSpinM.setValueSilent(m)
        self.fromSpinS.setValueSilent(s)
        self.validateCropRange()

    def setToSpin(self, h, m, s):
        self.toSpinH.setValueSilent(h)
        self.toSpinM.setValueSilent(m)
        self.toSpinS.setValueSilent(s)
        self.validateCropRange()

    def checkCropRange(self, h, m, s, maximum=None, minimum=None):
        videoTotalSeconds = self.downloadInfo.videoData.lengthSeconds
        if maximum == None:
            maximum = videoTotalSeconds
        if minimum == None:
            minimum = 0
        totalSeconds = Utils.toSeconds(h, m, s)
        if totalSeconds > maximum:
            return Utils.toTime(maximum)
        elif totalSeconds < minimum:
            return Utils.toTime(minimum)
        else:
            return Utils.toTime(totalSeconds)

    def reloadCropArea(self):
        self.fromTimeBar.setEnabled(not self.cropFromStartRadioButton.isChecked())
        self.toTimeBar.setEnabled(not self.cropToEndRadioButton.isChecked())
        if self.cropFromStartRadioButton.isChecked():
            self.setFromSpin(0, 0, 0)
        if self.cropToEndRadioButton.isChecked():
            self.setToSpin(*Utils.toTime(self.downloadInfo.videoData.lengthSeconds))
        self.reloadCropInfoArea()

    def reloadCropInfoArea(self):
        hasCropRange = self.cropFromSelectRadioButton.isChecked() or self.cropToSelectRadioButton.isChecked()
        showSettingsInfo = hasCropRange and not self.clippingModeCheckBox.isChecked()
        showRangeInfo = self.isCropRangeInvalid()
        self.cropInfoArea.setCurrentIndex(1 if showRangeInfo else 0)
        self.cropInfoArea.setVisible(showRangeInfo or showSettingsInfo)
        if not hasCropRange:
            self.clippingModeCheckBox.setChecked(False)
        self.clippingModeArea.setEnabled(hasCropRange)

    def checkUpdateTrack(self):
        self.reloadCropArea()
        if self.updateTrackCheckBox.isChecked() and not self.cropToEndRadioButton.isChecked():
            if self.ask("warning", "#Update track mode is currently enabled.\nSetting the end of the crop range will not track updates.\nProceed?", defaultOk=True):
                self.updateTrackCheckBox.setCheckState(QtCore.Qt.Unchecked)
            else:
                self.cropToEndRadioButton.setChecked(True)

    def showCropInfo(self):
        self.info("information", T("#This will crop the video at a point near this range that requires less computation.\nThis may result in an error of seconds.\nActivate '{menuName}' for accurate processing.", menuName=T("clipping-mode")), contentTranslate=False)

    def showClippingModeInfo(self):
        infoString = T("#Re-encodes the file to produce a video of the specified range.\nThis increases the computation of the encoding process and consumes a lot of time.")
        warningString = T("#This operation is resource intensive.\nDepending on your PC specifications, the performance of other processes may be affected.\n\nIf the video has corrupted parts, this may cause errors.")
        self.info("information", f"{infoString}\n\n{warningString}", contentTranslate=False)

    def setClippingMode(self, clippingMode):
        self.downloadInfo.setClippingModeEnabled(clippingMode)
        self.reloadCropInfoArea()
        if clippingMode:
            self.info("warning", "#This operation is resource intensive.\nDepending on your PC specifications, the performance of other processes may be affected.\n\nIf the video has corrupted parts, this may cause errors.")

    def askSaveAs(self):
        directory = self.downloadInfo.getAbsoluteFileName()
        filters = self.downloadInfo.getAvailableFormats()
        initialFilter = self.downloadInfo.fileFormat
        newDirectory = Utils.askSaveAs(directory, filters, initialFilter, parent=self)
        if newDirectory != None:
            self.downloadInfo.setAbsoluteFileName(newDirectory)
            self.reloadFileDirectory()

    def showUnmuteVideoInfo(self):
        self.info("information", "#If there are no problems with the sound source used, or if there are parts that have been muted in error despite having permission to use them, you can use this function to unmute them.\nIn some cases, unmute may not be successful.")

    def showUpdateTrackInfo(self):
        self.info("information", "#Downloads the live replay continuously until the broadcast ends.\nThe download ends if there are no changes in the video for a certain amount of time.")

    def showPrioritizeInfo(self):
        self.info("information", "#This download will be prioritized. Downloads with this option take precedence over those without.")

    def setUpdateTrack(self, updateTrack):
        self.downloadInfo.setUpdateTrackEnabled(updateTrack)
        if self.updateTrackCheckBox.isChecked() and not self.cropToEndRadioButton.isChecked():
            if self.ask("warning", "#The end of the crop range is currently set.\nEnabling update track mode will ignore the end of the crop range and continue downloading.\nProceed?", defaultOk=True):
                self.cropToEndRadioButton.setChecked(True)
            else:
                self.updateTrackCheckBox.setCheckState(QtCore.Qt.Unchecked)

    def saveCropRange(self):
        self.downloadInfo.setCropRange(
            None if self.cropFromStartRadioButton.isChecked() else Utils.toSeconds(*self.getFromSpin()) * 1000,
            None if self.cropToEndRadioButton.isChecked() else Utils.toSeconds(*self.getToSpin()) * 1000
        )

    def accept(self):
        downloadAvailableState = DownloadChecker.isDownloadAvailable(self.downloadInfo, parent=self)
        if downloadAvailableState == DownloadChecker.State.AVAILABLE:
            if self.downloadInfo.type.isVideo():
                self.saveCropRange()
            self.downloadInfo.saveOptionHistory()
            super().accept(self.downloadInfo)
        elif downloadAvailableState == DownloadChecker.State.NEED_NEW_FILE_NAME:
            self.askSaveAs()