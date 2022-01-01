from Core.App import App
from Core.Ui import *
from Services.Messages import Messages


class DownloadMenu(QtWidgets.QDialog, UiFile.downloadMenu):
    def __init__(self, downloadInfo, showMore=True):
        super().__init__(parent=App.getActiveWindow())
        self.ignoreKey(QtCore.Qt.Key_Return, QtCore.Qt.Key_Enter)
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint)
        self.downloadInfo = downloadInfo
        Utils.setPlaceholder(self.videoWidgetPlaceholder, Ui.VideoWidget(self.downloadInfo.videoData, showMore=showMore))
        self.loadOptions()

    def loadOptions(self):
        self.window_title.setText(T("#Download {type}", type=T(self.downloadInfo.type.toString())))
        self.reloadFileDirectory()
        self.searchDirectory.clicked.connect(self.askSaveDirectory)
        self.resolution.addItems(self.downloadInfo.accessToken.getResolutions())
        self.resolution.setCurrentIndex(0)
        self.resolution.currentIndexChanged.connect(self.setResolution)
        self.settings.clicked.connect(self.openSettings)
        if self.downloadInfo.type.isStream():
            self.cropArea.hide()
        elif self.downloadInfo.type.isVideo():
            self.setupCropArea()
            h, m, s = Utils.toTime(self.downloadInfo.videoData.lengthSeconds.totalSeconds())
            self.startSpinH.setMaximum(h + 1)
            self.endSpinH.setMaximum(h + 1)
            self.reloadCropArea()
        else:
            self.cropArea.hide()

    def reloadFileDirectory(self):
        self.currentDirectory.setText(self.downloadInfo.getAbsoluteFileName())
        self.currentDirectory.setCursorPosition(0)

    def setResolution(self, resolution):
        self.downloadInfo.setResolution(resolution)
        self.reloadFileDirectory()
        if self.downloadInfo.checkResolutionInFileName():
            if Utils.ask("filename-change", "#The filename template contains a 'resolution' variable. Do you want to create a new filename based on the changed resolution?", defaultOk=True):
                self.downloadInfo.setFileName(self.downloadInfo.createFileName())
                self.reloadFileDirectory()

    def setupCropArea(self):
        self.cropArea.setTitle("{} / {}".format(T("crop"), T("#Total Length : {duration}", duration=self.downloadInfo.videoData.lengthSeconds)))
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
        self.warnUpdateTrack()

    def warnUpdateTrack(self):
        if DB.download.isUpdateTrackEnabled():
            if not self.endCheckBox.isChecked():
                if not Utils.ask("warning", "#Update track mode is currently enabled.\nSetting the end of the crop range will not track updates.\nProceed?", defaultOk=True):
                    self.endCheckBox.click()

    def showCropInfo(self):
        Utils.info("video-crop", "#Video crop is based on the closest point in the crop range that can be processed.")

    def askSaveDirectory(self):
        DB.temp.updateDefaultDirectory()
        self.downloadInfo.setDirectory(DB.temp.getDefaultDirectory())
        self.reloadFileDirectory()
        directory = self.downloadInfo.getAbsoluteFileName()
        filters = self.downloadInfo.getAvailableFormats()
        initialFilter = self.downloadInfo.fileFormat
        newDirectory = Utils.askSaveDirectory(directory, filters, initialFilter)
        if newDirectory != None:
            self.downloadInfo.setAbsoluteFileName(newDirectory)
            self.reloadFileDirectory()

    def accept(self):
        if self.downloadInfo.type.isVideo():
            self.saveCropRange()
        if Utils.isFile(self.downloadInfo.getAbsoluteFileName()):
            if not Utils.ask(*Messages.ASK.FILE_OVERWRITE):
                return
        elif not Utils.isDirectory(self.downloadInfo.directory) or Utils.isDirectory(self.downloadInfo.getAbsoluteFileName()):
            Utils.info(*Messages.INFO.UNAVAILABLE_FILENAME_OR_DIRECTORY)
            self.askSaveDirectory()
            return
        return super().accept(self.downloadInfo)

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

    def openSettings(self):
        oldTemplateString = self.downloadInfo.getFileNameTemplate()
        oldUpdateTrack = DB.download.isUpdateTrackEnabled()
        App.coreWindow().openSettings(page=2)
        if oldTemplateString != self.downloadInfo.getFileNameTemplate():
            if Utils.ask("filename-change", "#The filename template has been changed. Do you want to create a new filename based on the changed template?", defaultOk=True):
                self.downloadInfo.setFileName(self.downloadInfo.createFileName())
                self.reloadFileDirectory()
        if oldUpdateTrack != DB.download.isUpdateTrackEnabled():
            self.warnUpdateTrack()