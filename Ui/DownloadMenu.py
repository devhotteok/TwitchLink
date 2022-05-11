from Core.Ui import *
from Services.Messages import Messages
from Download.DownloadManager import DownloadManager


class DownloadMenu(QtWidgets.QDialog, UiFile.downloadMenu, WindowGeometryManager):
    def __init__(self, downloadInfo, viewOnly=False, parent=None):
        super(DownloadMenu, self).__init__(parent=parent)
        self.finished.connect(self.saveWindowGeometry)
        self.ignoreKey(QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter)
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint)
        self.downloadInfo = downloadInfo
        self.setWindowGeometryKey(f"{self.getWindowGeometryKey()}/{self.downloadInfo.type.toString()}")
        self.loadWindowGeometry()
        self.videoWidget = Utils.setPlaceholder(self.videoWidget, Ui.VideoWidget(self.downloadInfo.videoData, viewOnly=viewOnly, parent=self))
        self.loadOptions()

    def loadOptions(self):
        self.window_title.setText(T("#Download {type}", type=T(self.downloadInfo.type.toString())))
        self.reloadFileDirectory()
        self.fileFormat.currentTextChanged.connect(self.setFormat)
        self.searchDirectory.clicked.connect(self.askSaveDirectory)
        for resolution in self.downloadInfo.accessToken.getResolutions():
            self.resolution.addItem(resolution.displayName, resolution)
        self.resolution.setCurrentIndex(0)
        self.resolution.currentIndexChanged.connect(self.setResolution)
        if self.downloadInfo.type.isStream():
            self.cropArea.hide()
            self.advancedArea.hide()
        elif self.downloadInfo.type.isVideo():
            self.setupCropArea()
            h, m, s = Utils.toTime(self.downloadInfo.videoData.lengthSeconds.totalSeconds())
            self.startSpinH.setMaximum(h + 1)
            self.endSpinH.setMaximum(h + 1)
            self.reloadCropArea()
            self.unmuteVideoCheckBox.setChecked(self.downloadInfo.isUnmuteVideoEnabled())
            self.unmuteVideoCheckBox.toggled.connect(self.downloadInfo.setUnmuteVideoEnabled)
            self.unmuteVideoInfo.clicked.connect(self.showUnmuteVideoInfo)
            self.updateTrackCheckBox.setChecked(self.downloadInfo.isUpdateTrackEnabled())
            self.updateTrackCheckBox.toggled.connect(self.setUpdateTrack)
            self.updateTrackInfo.clicked.connect(self.showUpdateTrackInfo)
            self.prioritizeCheckBox.toggled.connect(self.downloadInfo.setPrioritizeEnabled)
            self.prioritizeInfo.clicked.connect(self.showPrioritizeInfo)
        else:
            self.cropArea.hide()
            self.unmuteVideoArea.hide()
            self.updateTrackArea.hide()
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
        self.downloadInfo.setResolution(self.resolution.itemData(index))
        self.reloadFileDirectory()
        if self.downloadInfo.checkResolutionInFileName():
            if self.ask("filename-change", "#The filename template contains a 'resolution' variable. Do you want to create a new filename based on the changed resolution?", defaultOk=True):
                self.downloadInfo.setFileName(self.downloadInfo.createFileName())
                self.reloadFileDirectory()

    def setupCropArea(self):
        self.cropArea.setTitle(f"{T('crop')} / {T('#Total Length: {duration}', duration=self.downloadInfo.videoData.lengthSeconds)}")
        self.startCheckBox.stateChanged.connect(self.reloadCropArea)
        self.endCheckBox.stateChanged.connect(self.checkUpdateTrack)
        self.startSpinH.valueChanged.connect(self.reloadStartRange)
        self.startSpinM.valueChanged.connect(self.reloadStartRange)
        self.startSpinS.valueChanged.connect(self.reloadStartRange)
        self.endSpinH.valueChanged.connect(self.reloadEndRange)
        self.endSpinM.valueChanged.connect(self.reloadEndRange)
        self.endSpinS.valueChanged.connect(self.reloadEndRange)
        self.cropInfo.clicked.connect(self.showCropInfo)

    def reloadStartRange(self):
        self.setStartSpin(*self.checkCropRange(*self.getStartSpin(), maximum=Utils.toSeconds(*self.getEndSpin())))

    def reloadEndRange(self):
        self.setEndSpin(*self.checkCropRange(*self.getEndSpin(), minimum=Utils.toSeconds(*self.getStartSpin())))

    def getStartSpin(self):
        return self.startSpinH.value(), self.startSpinM.value(), self.startSpinS.value()

    def getEndSpin(self):
        return self.endSpinH.value(), self.endSpinM.value(), self.endSpinS.value()

    def setStartSpin(self, h, m, s):
        self.startSpinH.setValueSilent(h)
        self.startSpinM.setValueSilent(m)
        self.startSpinS.setValueSilent(s)

    def setEndSpin(self, h, m, s):
        self.endSpinH.setValueSilent(h)
        self.endSpinM.setValueSilent(m)
        self.endSpinS.setValueSilent(s)

    def checkCropRange(self, h, m, s, maximum=None, minimum=None):
        videoTotalSeconds = self.downloadInfo.videoData.lengthSeconds.totalSeconds()
        if maximum == None:
            maximum = videoTotalSeconds
        else:
            maximum = min(maximum, videoTotalSeconds)
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
        self.startTimeBar.setEnabled(not self.startCheckBox.isChecked())
        self.endTimeBar.setEnabled(not self.endCheckBox.isChecked())
        if self.startCheckBox.isChecked():
            self.setStartSpin(0, 0, 0)
        if self.endCheckBox.isChecked():
            self.setEndSpin(*Utils.toTime(self.downloadInfo.videoData.lengthSeconds.totalSeconds()))

    def checkUpdateTrack(self):
        self.reloadCropArea()
        if self.updateTrackCheckBox.isChecked() and not self.endCheckBox.isChecked():
            if self.ask("warning", "#Update track mode is currently enabled.\nSetting the end of the crop range will not track updates.\nProceed?", defaultOk=True):
                self.updateTrackCheckBox.setCheckState(QtCore.Qt.Unchecked)
            else:
                self.endCheckBox.setCheckState(QtCore.Qt.Checked)

    def showCropInfo(self):
        self.info("video-crop", "#Video crop is based on the closest point in the crop range that can be processed.")

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
        self.info("information", "#Downloads the live replay continuously until the live broadcast ends.\nThe download ends if there are no changes in the video for a certain amount of time.")

    def showPrioritizeInfo(self):
        self.info("information", "#This download will be prioritized. Downloads with this option take precedence over those without.")

    def setUpdateTrack(self, updateTrack):
        self.downloadInfo.setUpdateTrackEnabled(updateTrack)
        if self.updateTrackCheckBox.isChecked() and not self.endCheckBox.isChecked():
            if self.ask("warning", "#The end of the crop range is currently set.\nEnabling update track mode will ignore the end of the crop range and continue downloading.\nProceed?", defaultOk=True):
                self.endCheckBox.setCheckState(QtCore.Qt.Checked)
            else:
                self.updateTrackCheckBox.setCheckState(QtCore.Qt.Unchecked)

    def isFileNameDuplicate(self):
        for downloader in DownloadManager.getRunningDownloaders():
            if downloader.setup.downloadInfo.getAbsoluteFileName() == self.downloadInfo.getAbsoluteFileName():
                return True
        return False

    def checkNetworkInstability(self):
        if self.downloadInfo.type.isStream():
            if DownloadManager.isDownloaderRunning():
                return self.warnNetworkInstability("download", "live")
        else:
            for downloader in DownloadManager.getRunningDownloaders():
                if downloader.setup.downloadInfo.type.isStream():
                    return self.warnNetworkInstability("live-download", self.downloadInfo.type.toString())
        return True

    def warnNetworkInstability(self, downloadType, operationType):
        return self.ask("warning", T("#You already have one or more {downloadType}s in progress.\nDepending on the network specifications, if you proceed with the {operationType} download, the live download may become unstable or interrupted.\nProceed?", downloadType=T(downloadType), operationType=T(operationType)), contentTranslate=False)

    def accept(self):
        if self.downloadInfo.type.isVideo():
            self.saveCropRange()
        if self.isFileNameDuplicate():
            self.info("error", "#There is another download in progress with the same file name.")
            self.askSaveDirectory()
            return
        elif Utils.isFile(self.downloadInfo.getAbsoluteFileName()):
            if not self.ask(*Messages.ASK.FILE_OVERWRITE):
                return
        elif not Utils.isDirectory(self.downloadInfo.directory) or Utils.isDirectory(self.downloadInfo.getAbsoluteFileName()):
            self.info(*Messages.INFO.UNAVAILABLE_FILENAME_OR_DIRECTORY)
            self.askSaveDirectory()
            return
        if not self.checkNetworkInstability():
            return
        self.downloadInfo.saveHistory()
        super().accept(self.downloadInfo)

    def saveCropRange(self):
        if self.startCheckBox.isChecked():
            start = None
        else:
            start = Utils.toSeconds(*self.getStartSpin())
        if self.endCheckBox.isChecked():
            end = None
        else:
            end = Utils.toSeconds(*self.getEndSpin())
        self.downloadInfo.setCropRange(start, end)