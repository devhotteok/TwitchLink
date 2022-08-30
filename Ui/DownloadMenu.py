from Core.Ui import *
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator
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
        self.alertIcon = Utils.setSvgIcon(self.alertIcon, Icons.ALERT_RED_ICON)
        self.loadOptions()

    def loadOptions(self):
        self.windowTitleLabel.setText(T("#Download {type}", type=T(self.downloadInfo.type.toString())))
        self.reloadFileDirectory()
        self.fileFormat.currentTextChanged.connect(self.setFormat)
        self.searchDirectory.clicked.connect(self.askSaveDirectory)
        for resolution in self.downloadInfo.accessToken.getResolutions():
            self.resolution.addItem(resolution.displayName)
        self.resolution.setCurrentIndex(self.downloadInfo.selectedResolutionIndex)
        self.resolution.currentIndexChanged.connect(self.setResolution)
        if self.downloadInfo.type.isStream():
            self.cropArea.hide()
            self.unmuteVideoArea.hide()
            self.updateTrackArea.hide()
            self.prioritizeArea.hide()
            self.optimizeFileCheckBox.setChecked(self.downloadInfo.isOptimizeFileEnabled())
            self.optimizeFileCheckBox.toggled.connect(self.setOptimizeFile)
            self.optimizeFileInfo.clicked.connect(self.showOptimizeFileInfo)
        elif self.downloadInfo.type.isVideo():
            self.setupCropArea()
            self.unmuteVideoCheckBox.setChecked(self.downloadInfo.isUnmuteVideoEnabled())
            self.unmuteVideoCheckBox.toggled.connect(self.downloadInfo.setUnmuteVideoEnabled)
            self.unmuteVideoInfo.clicked.connect(self.showUnmuteVideoInfo)
            self.updateTrackCheckBox.setChecked(self.downloadInfo.isUpdateTrackEnabled())
            self.updateTrackCheckBox.toggled.connect(self.setUpdateTrack)
            self.updateTrackInfo.clicked.connect(self.showUpdateTrackInfo)
            self.optimizeFileCheckBox.setChecked(self.downloadInfo.isOptimizeFileEnabled())
            self.optimizeFileCheckBox.toggled.connect(self.setOptimizeFile)
            self.optimizeFileInfo.clicked.connect(self.showOptimizeFileInfo)
            self.prioritizeCheckBox.setChecked(self.downloadInfo.isPrioritizeEnabled())
            self.prioritizeCheckBox.toggled.connect(self.downloadInfo.setPrioritizeEnabled)
            self.prioritizeInfo.clicked.connect(self.showPrioritizeInfo)
            self.reloadCropArea()
        else:
            self.cropArea.hide()
            self.unmuteVideoArea.hide()
            self.updateTrackArea.hide()
            self.optimizeFileArea.hide()
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
        self.fromSpinH.valueChanged.connect(self.reloadStartRange)
        self.fromSpinM.valueChanged.connect(self.reloadStartRange)
        self.fromSpinS.valueChanged.connect(self.reloadStartRange)
        self.toSpinH.valueChanged.connect(self.reloadEndRange)
        self.toSpinM.valueChanged.connect(self.reloadEndRange)
        self.toSpinS.valueChanged.connect(self.reloadEndRange)
        self.cropInfo.clicked.connect(self.showCropInfo)
        h, m, s = Utils.toTime(self.downloadInfo.videoData.lengthSeconds)
        self.fromSpinH.setMaximum(h + 1)
        self.toSpinH.setMaximum(h + 1)
        if self.downloadInfo.range[0] != None:
            self.cropFromSelectRadioButton.setChecked(True)
            self.setFromSpin(*Utils.toTime(self.downloadInfo.range[0] / 1000))
        if self.downloadInfo.range[1] != None:
            self.cropToSelectRadioButton.setChecked(True)
            self.setToSpin(*Utils.toTime(self.downloadInfo.range[1] / 1000))

    def reloadStartRange(self):
        fromSpinSeconds = Utils.toSeconds(*self.getFromSpin())
        toSpinSeconds = Utils.toSeconds(*self.getToSpin())
        if fromSpinSeconds >= toSpinSeconds:
            self.setToSpin(*self.checkCropRange(*Utils.toTime(fromSpinSeconds + 1)))
        self.setFromSpin(*self.checkCropRange(*self.getFromSpin(), maximum=self.downloadInfo.videoData.lengthSeconds - 1))

    def reloadEndRange(self):
        fromSpinSeconds = Utils.toSeconds(*self.getFromSpin())
        toSpinSeconds = Utils.toSeconds(*self.getToSpin())
        if fromSpinSeconds >= toSpinSeconds:
            self.setFromSpin(*self.checkCropRange(*Utils.toTime(toSpinSeconds - 1)))
        self.setToSpin(*self.checkCropRange(*self.getToSpin(), minimum=1))

    def getFromSpin(self):
        return self.fromSpinH.value(), self.fromSpinM.value(), self.fromSpinS.value()

    def getToSpin(self):
        return self.toSpinH.value(), self.toSpinM.value(), self.toSpinS.value()

    def setFromSpin(self, h, m, s):
        self.fromSpinH.setValueSilent(h)
        self.fromSpinM.setValueSilent(m)
        self.fromSpinS.setValueSilent(s)

    def setToSpin(self, h, m, s):
        self.toSpinH.setValueSilent(h)
        self.toSpinM.setValueSilent(m)
        self.toSpinS.setValueSilent(s)

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
        self.cropInfoArea.setVisible((self.cropFromSelectRadioButton.isChecked() or self.cropToSelectRadioButton.isChecked()) and not self.optimizeFileCheckBox.isChecked())

    def checkUpdateTrack(self):
        self.reloadCropArea()
        if self.updateTrackCheckBox.isChecked() and not self.cropToEndRadioButton.isChecked():
            if self.ask("warning", "#Update track mode is currently enabled.\nSetting the end of the crop range will not track updates.\nProceed?", defaultOk=True):
                self.updateTrackCheckBox.setCheckState(QtCore.Qt.Unchecked)
            else:
                self.cropToEndRadioButton.setChecked(True)

    def showCropInfo(self):
        self.info("information", T("#This will crop the video at a point near this range that requires less computation.\nThis may result in an error of seconds.\nActivate '{menuName}' for accurate processing.", menuName=T("optimize-file")), contentTranslate=False)

    def askSaveDirectory(self):
        directory = self.downloadInfo.getAbsoluteFileName()
        filters = self.downloadInfo.getAvailableFormats()
        initialFilter = self.downloadInfo.fileFormat
        newDirectory = Utils.askSaveDirectory(directory, filters, initialFilter, parent=self)
        if newDirectory != None:
            self.downloadInfo.setAbsoluteFileName(newDirectory)
            self.reloadFileDirectory()

    def showUnmuteVideoInfo(self):
        self.info("information", "#If there are no problems with the sound source used, or if there are parts that have been muted in error despite having permission to use them, you can use this function to unmute them.\nIn some cases, unmute may not be successful.")

    def showUpdateTrackInfo(self):
        self.info("information", "#Downloads the live replay continuously until the broadcast ends.\nThe download ends if there are no changes in the video for a certain amount of time.")

    def showOptimizeFileInfo(self):
        infoString = T("#Maintains {videoType} quality but reduces file size.\nThis increases the computation of the encoding process and consumes a lot of time.", videoType=T(self.downloadInfo.type.toString()))
        warningString = T("#This operation is resource intensive.\nDepending on your PC specifications, the performance of other processes may be affected.\n\nIf the {videoType} file has corrupted parts, this may cause errors.", videoType=T(self.downloadInfo.type.toString()))
        optionInfoString = T("#Depending on the streamer's broadcast settings, this option may not have any effect." if self.downloadInfo.type.isStream() else "#Depending on the video properties, this option may not have any effect.")
        self.info("information", f"{infoString}\n\n{warningString}\n\n{optionInfoString}", contentTranslate=False)

    def showPrioritizeInfo(self):
        self.info("information", "#This download will be prioritized. Downloads with this option take precedence over those without.")

    def setUpdateTrack(self, updateTrack):
        self.downloadInfo.setUpdateTrackEnabled(updateTrack)
        if self.updateTrackCheckBox.isChecked() and not self.cropToEndRadioButton.isChecked():
            if self.ask("warning", "#The end of the crop range is currently set.\nEnabling update track mode will ignore the end of the crop range and continue downloading.\nProceed?", defaultOk=True):
                self.cropToEndRadioButton.setChecked(True)
            else:
                self.updateTrackCheckBox.setCheckState(QtCore.Qt.Unchecked)

    def setOptimizeFile(self, optimizeFile):
        self.downloadInfo.setOptimizeFileEnabled(optimizeFile)
        if self.downloadInfo.type.isVideo():
            self.reloadCropInfoArea()
        if optimizeFile:
            self.info("warning", T("#This operation is resource intensive.\nDepending on your PC specifications, the performance of other processes may be affected.\n\nIf the {videoType} file has corrupted parts, this may cause errors.", videoType=T(self.downloadInfo.type.toString())), contentTranslate=False)

    def accept(self):
        downloadAvailableState = DownloadChecker.isDownloadAvailable(self.downloadInfo, parent=self)
        if downloadAvailableState == DownloadChecker.State.AVAILABLE:
            if self.downloadInfo.type.isVideo():
                self.saveCropRange()
            self.downloadInfo.saveOptionHistory()
            super().accept(self.downloadInfo)
        elif downloadAvailableState == DownloadChecker.State.NEED_NEW_FILE_NAME:
            self.askSaveDirectory()

    def saveCropRange(self):
        if self.cropFromStartRadioButton.isChecked():
            start = None
        else:
            start = Utils.toSeconds(*self.getFromSpin()) * 1000
        if self.cropToEndRadioButton.isChecked():
            end = None
        else:
            end = Utils.toSeconds(*self.getToSpin()) * 1000
        self.downloadInfo.setCropRange(start, end)