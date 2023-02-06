from Core.Ui import *
from Services.Twitch.Gql.TwitchGqlModels import Stream
from Services.Twitch.Playback.TwitchPlaybackModels import StreamUrl
from Download.ScheduledDownloadPreset import ScheduledDownloadPreset
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator

from datetime import datetime


class ScheduledDownloadSettings(QtWidgets.QDialog, UiFile.scheduledDownloadSettings, WindowGeometryManager):
    def __init__(self, scheduledDownloadPreset=None, parent=None):
        super(ScheduledDownloadSettings, self).__init__(parent=parent)
        self.isEditMode = scheduledDownloadPreset != None
        self.finished.connect(self.saveWindowGeometry)
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint)
        self.loadWindowGeometry()
        self.scheduledDownloadPreset = scheduledDownloadPreset if self.isEditMode else ScheduledDownloadPreset()
        self.virtualPreset = scheduledDownloadPreset.copy() if self.isEditMode else self.scheduledDownloadPreset
        self.channelEdit.setText(self.virtualPreset.channel)
        self.channelEdit.setEnabled(not self.isEditMode)
        self.channelEdit.textChanged.connect(self.channelChanged)
        self.reloadDirectory()
        self.searchDirectory.clicked.connect(self.askDirectory)
        self.filenameTemplate.setText(self.virtualPreset.filenameTemplate)
        self.filenameTemplate.textChanged.connect(self.filenameTemplateChanged)
        self.filenameTemplateInfo.clicked.connect(self.showStreamTemplateInfo)
        self.reloadFileFormat()
        self.fileFormat.currentTextChanged.connect(self.fileFormatChanged)
        for quality in self.virtualPreset.getQualityList():
            self.preferredQuality.addItem(quality.toString() if quality.isValid() else T(quality.toString()))
        self.preferredQuality.setCurrentIndex(self.virtualPreset.preferredQualityIndex)
        self.preferredQuality.currentIndexChanged.connect(self.preferredQualityChanged)
        for frameRate in self.virtualPreset.getFrameRateList():
            self.preferredFrameRate.addItem(frameRate.toString() if frameRate.isValid() else T(frameRate.toString()))
        self.preferredFrameRate.setCurrentIndex(self.virtualPreset.preferredFrameRateIndex)
        self.preferredFrameRate.currentIndexChanged.connect(self.preferredFrameRateChanged)
        self.preferredResolutionOnlyCheckBox.setChecked(self.virtualPreset.isPreferredResolutionOnlyEnabled())
        self.preferredResolutionOnlyCheckBox.toggled.connect(self.virtualPreset.setPreferredResolutionOnlyEnabled)
        self.preferredResolutionOnlyInfo.clicked.connect(self.showPreferredResolutionOnlyInfo)
        self.nextDownloadLabel.setVisible(self.isEditMode)
        self.updateFilenamePreview()

    def channelChanged(self, text):
        channel = text.lower()
        self.virtualPreset.setChannel(channel)
        self.updateFilenamePreview()

    def reloadDirectory(self):
        self.currentDirectory.setText(self.virtualPreset.directory)
        self.currentDirectory.setToolTip(self.virtualPreset.directory)

    def askDirectory(self):
        newDirectory = Utils.askDirectory(self.virtualPreset.directory, parent=self)
        if newDirectory != None:
            self.virtualPreset.setDirectory(newDirectory)
            self.reloadDirectory()

    def filenameTemplateChanged(self, text):
        self.virtualPreset.setFilenameTemplate(text)
        self.updateFilenamePreview()

    def showStreamTemplateInfo(self):
        Ui.PropertyView(
            FileNameGenerator.getInfoTitle("stream"),
            None,
            FileNameGenerator.getStreamFileNameTemplateFormData(),
            enableLabelSelection=True,
            enableFieldTranslation=True,
            parent=self
        ).exec()

    def fileFormatChanged(self, text):
        self.virtualPreset.setFileFormat(text)
        self.updateFilenamePreview()

    def reloadFileFormat(self):
        self.fileFormat.blockSignals(True)
        self.fileFormat.clear()
        self.fileFormat.addItems(self.virtualPreset.getAvailableFormats())
        self.fileFormat.setCurrentText(self.virtualPreset.fileFormat)
        self.fileFormat.blockSignals(False)

    def preferredQualityChanged(self, index):
        self.virtualPreset.setPreferredQuality(index)
        self.reloadFileFormat()
        self.updateFilenamePreview()

    def preferredFrameRateChanged(self, index):
        self.virtualPreset.setPreferredFrameRate(index)
        self.updateFilenamePreview()

    def showPreferredResolutionOnlyInfo(self):
        self.info("information", "#If enabled, the download will not be performed until a matching resolution is found.\nIf disabled, it automatically selects a different resolution.")

    def createPreviewStream(self):
        return Stream({
            "id": "0",
            "title": "Stream Title",
            "game": {
                "displayName": "Just Chatting"
            },
            "broadcaster": {
                "login": self.virtualPreset.channel,
                "displayName": self.virtualPreset.channel
            },
            "createdAt": datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ"),
            "viewersCount": 0
        })

    def createPreviewResolution(self):
        return self.virtualPreset.selectResolution([
            StreamUrl(self.virtualPreset.channel, "1080p60", "chunked", ""),
            StreamUrl(self.virtualPreset.channel, "1080p30", "1080p30", ""),
            StreamUrl(self.virtualPreset.channel, "720p60", "720p60", ""),
            StreamUrl(self.virtualPreset.channel, "720p30", "720p30", ""),
            StreamUrl(self.virtualPreset.channel, "480p", "480p", ""),
            StreamUrl(self.virtualPreset.channel, "360p", "360p", ""),
            StreamUrl(self.virtualPreset.channel, "160p", "160p", ""),
            StreamUrl(self.virtualPreset.channel, "audio_only", "audio_only", "")
        ])

    def updateFilenamePreview(self):
        self.filenamePreview.setText(FileNameGenerator.generateFileName(self.createPreviewStream(), self.createPreviewResolution(), customTemplate=f"{self.virtualPreset.filenameTemplate}.{self.virtualPreset.fileFormat}"))

    def savePreset(self):
        self.scheduledDownloadPreset.channel = self.virtualPreset.channel
        self.scheduledDownloadPreset.directory = self.virtualPreset.directory
        self.scheduledDownloadPreset.filenameTemplate = self.virtualPreset.filenameTemplate
        self.scheduledDownloadPreset.fileFormat = self.virtualPreset.fileFormat
        self.scheduledDownloadPreset.preferredQualityIndex = self.virtualPreset.preferredQualityIndex
        self.scheduledDownloadPreset.preferredFrameRateIndex = self.virtualPreset.preferredFrameRateIndex
        self.scheduledDownloadPreset.preferredResolutionOnly = self.virtualPreset.preferredResolutionOnly

    def accept(self):
        formCheck = []
        if self.virtualPreset.channel == "":
            formCheck.append(T("channel"))
        if self.virtualPreset.filenameTemplate == "":
            formCheck.append(T("filename-template"))
        if len(formCheck) == 0:
            self.savePreset()
            self.scheduledDownloadPreset.saveOptionHistory()
            super().accept(self.scheduledDownloadPreset)
        else:
            formInfo = "\n".join(formCheck)
            self.info("warning", f"{T('#Some fields are empty.')}\n\n{formInfo}", contentTranslate=False)