from Core.Ui import *
from Services.Playlist.Resolution import Resolution
from Services.Twitch.GQL import TwitchGQLModels
from Search.QueryParser import TwitchQueryParser
from Download.ScheduledDownloadPreset import ScheduledDownloadPreset
from Ui.Components.Utils.FileNameGenerator import FileNameGenerator
from Ui.Components.Widgets.FileNameTemplateInfo import FileNameTemplateInfo


class ScheduledDownloadSettings(QtWidgets.QDialog, WindowGeometryManager):
    scheduledDownloadUpdated = QtCore.pyqtSignal(ScheduledDownloadPreset)

    def __init__(self, scheduledDownloadPreset: ScheduledDownloadPreset | None = None, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.isEditMode = scheduledDownloadPreset != None
        self.scheduledDownloadPreset = scheduledDownloadPreset if self.isEditMode else ScheduledDownloadPreset()
        self._ui = UiLoader.load("scheduledDownloadSettings", self)
        self.finished.connect(self.saveWindowGeometry)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowMaximizeButtonHint)
        self.loadWindowGeometry()
        self.virtualPreset = scheduledDownloadPreset.copy() if self.isEditMode else self.scheduledDownloadPreset
        self._ui.channelEdit.setText(self.virtualPreset.channel)
        self._ui.channelEdit.setEnabled(not self.isEditMode)
        self._ui.channelEdit.textChanged.connect(self.channelChanged)
        self.reloadDirectory()
        self._ui.searchDirectory.clicked.connect(self.askDirectory)
        self.filenameTemplateInfoWindow = FileNameTemplateInfo(FileNameTemplateInfo.TYPE.STREAM, parent=self)
        self._ui.filenameTemplate.setText(self.virtualPreset.filenameTemplate)
        self._ui.filenameTemplate.textChanged.connect(self.filenameTemplateChanged)
        self._ui.filenameTemplateInfo.clicked.connect(self.filenameTemplateInfoWindow.show)
        Utils.setIconViewer(self._ui.filenameTemplateInfo, Icons.HELP)
        self.reloadFileFormat()
        self._ui.fileFormat.currentTextChanged.connect(self.fileFormatChanged)
        self._ui.filenamePreviewInfo.clicked.connect(self.showFilenamePreviewInfo)
        Utils.setIconViewer(self._ui.filenamePreviewInfo, Icons.HELP)
        for quality in self.virtualPreset.getQualityList():
            self._ui.preferredQuality.addItem(quality.toString())
        self._ui.preferredQuality.setCurrentIndex(self.virtualPreset.preferredQualityIndex)
        self._ui.preferredQuality.currentIndexChanged.connect(self.preferredQualityChanged)
        self._ui.preferredResolutionOnlyCheckBox.setChecked(self.virtualPreset.isPreferredResolutionOnlyEnabled())
        self._ui.preferredResolutionOnlyCheckBox.toggled.connect(self.virtualPreset.setPreferredResolutionOnlyEnabled)
        self._ui.preferredResolutionOnlyInfo.clicked.connect(self.showPreferredResolutionOnlyInfo)
        Utils.setIconViewer(self._ui.preferredResolutionOnlyInfo, Icons.HELP)
        self._ui.downloadChatCheckBox.setChecked(self.virtualPreset.isDownloadChatEnabled())
        self._ui.downloadChatCheckBox.toggled.connect(self.virtualPreset.setDownloadChatEnabled)
        self._ui.downloadChatCheckBox.toggled.connect(self.onDownloadChatToggled)
        self._ui.createSubfolderForDownloadsCheckBox.setChecked(self.virtualPreset.isCreateSubfolderForDownloadsEnabled())
        self._ui.createSubfolderForDownloadsCheckBox.toggled.connect(self.virtualPreset.setCreateSubfolderForDownloadsEnabled)
        
        self._ui.adBlockSkipSegmentsRadioButton.setChecked(self.virtualPreset.isSkipAdsEnabled())
        self._ui.adBlockAlternativeScreenRadioButton.setChecked(not self.virtualPreset.isSkipAdsEnabled())
        
        self._ui.adBlockSkipSegmentsRadioButton.toggled.connect(self.virtualPreset.setSkipAdsEnabled)
        self._ui.adBlockInfo.clicked.connect(self.showAdBlockInfo)
        Utils.setIconViewer(self._ui.adBlockInfo, Icons.HELP)
        self._ui.remuxRadioButton.setChecked(self.virtualPreset.isRemuxEnabled())
        self._ui.concatRadioButton.setChecked(not self.virtualPreset.isRemuxEnabled())
        self._ui.remuxRadioButton.toggled.connect(self.virtualPreset.setRemuxEnabled)
        self._ui.encoderInfo.clicked.connect(self.showEncoderInfo)
        Utils.setIconViewer(self._ui.encoderInfo, Icons.HELP)
        self._ui.nextDownloadLabel.setVisible(self.isEditMode)
        self.updateFilenamePreview()

    def channelChanged(self, text: str) -> None:
        channel = text.lower()
        self.virtualPreset.setChannel(channel)
        self.updateFilenamePreview()

    def reloadDirectory(self) -> None:
        self._ui.currentDirectory.setText(self.virtualPreset.directory)
        self._ui.currentDirectory.setToolTip(self.virtualPreset.directory)

    def askDirectory(self) -> None:
        newDirectory = Utils.askDirectory(self.virtualPreset.directory, parent=self)
        if newDirectory != None:
            self.virtualPreset.setDirectory(newDirectory)
            self.reloadDirectory()

    def filenameTemplateChanged(self, text: str) -> None:
        self.virtualPreset.setFilenameTemplate(text)
        self.updateFilenamePreview()

    def fileFormatChanged(self, text: str) -> None:
        self.virtualPreset.setFileFormat(text)
        self.updateFilenamePreview()

    def reloadFileFormat(self) -> None:
        self._ui.fileFormat.blockSignals(True)
        self._ui.fileFormat.clear()
        self._ui.fileFormat.addItems(self.virtualPreset.getAvailableFormats())
        self._ui.fileFormat.setCurrentText(self.virtualPreset.fileFormat)
        self._ui.fileFormat.blockSignals(False)

    def showFilenamePreviewInfo(self) -> None:
        Utils.info("information", T("info.#this_is_just_preview_some_values_may_be", properties=", ".join((f"{T('stream')} {T('id')}", T("title"), f"{T('channel')} {T('displayname')}"))), contentTranslate=False, parent=self)

    def preferredQualityChanged(self, index: int) -> None:
        self.virtualPreset.setPreferredQuality(index)
        self.reloadFileFormat()
        self.updateFilenamePreview()

    def showPreferredResolutionOnlyInfo(self) -> None:
        Utils.info("information", "errors.#please_note_that_certain_video_qualitie", parent=self)

    def showAdBlockInfo(self) -> None:
        skipSegmentsInfo = T("info.#_skip_segments_ads_are_skipped_but_stre")
        alternativeScreenInfo = T("info.#_alternative_screen_displays_alternate")
        Utils.info("information", f"{T("info.#if_commercials_are_broadcast_during_thi")}\n\n{skipSegmentsInfo}\n\n\n{alternativeScreenInfo}", contentTranslate=False, parent=self)

    def showEncoderInfo(self) -> None:
        remuxInfo = T("prompts.#_remux_file_will_be_saved_as_standard_v")
        concatInfo = T("errors.#_concat_this_feature_enables_you_store")
        Utils.info("information", f"{remuxInfo}\n\n\n{concatInfo}", contentTranslate=False, parent=self)

    def createPreviewStream(self) -> TwitchGQLModels.Stream:
        return TwitchGQLModels.Stream({
            "id": "0",
            "title": "Stream Title",
            "game": {
                "displayName": "Just Chatting"
            },
            "broadcaster": {
                "login": self.virtualPreset.channel,
                "displayName": self.virtualPreset.channel
            },
            "createdAt": QtCore.QDateTime.currentDateTimeUtc().toString("yyyy-MM-ddTHH:mm:ssZ"),
            "viewersCount": 0
        })

    def createPreviewResolution(self) -> Resolution:
        return self.virtualPreset.selectResolution([
            Resolution("1080p60", "chunked", QtCore.QUrl()),
            Resolution("1080p30", "1080p30", QtCore.QUrl()),
            Resolution("720p60", "720p60", QtCore.QUrl()),
            Resolution("720p30", "720p30", QtCore.QUrl()),
            Resolution("480p", "480p", QtCore.QUrl()),
            Resolution("360p", "360p", QtCore.QUrl()),
            Resolution("160p", "160p", QtCore.QUrl()),
            Resolution("audio_only", "audio_only", QtCore.QUrl())
        ])

    def updateFilenamePreview(self) -> None:
        self._ui.filenamePreview.setText(FileNameGenerator.generateFileName(self.createPreviewStream(), self.createPreviewResolution(), filenameTemplate=f"{self.virtualPreset.filenameTemplate}.{self.virtualPreset.fileFormat}"))

    def savePreset(self) -> None:
        self.scheduledDownloadPreset.channel = self.virtualPreset.channel
        self.scheduledDownloadPreset.directory = self.virtualPreset.directory
        self.scheduledDownloadPreset.filenameTemplate = self.virtualPreset.filenameTemplate
        self.scheduledDownloadPreset.fileFormat = self.virtualPreset.fileFormat
        self.scheduledDownloadPreset.preferredQualityIndex = self.virtualPreset.preferredQualityIndex
        self.scheduledDownloadPreset.preferredResolutionOnly = self.virtualPreset.preferredResolutionOnly
        self.scheduledDownloadPreset.skipAds = self.virtualPreset.skipAds
        self.scheduledDownloadPreset.remux = self.virtualPreset.remux
        self.scheduledDownloadPreset.downloadChat = self.virtualPreset.downloadChat
        self.scheduledDownloadPreset.createSubfolderForDownloads = self.virtualPreset.createSubfolderForDownloads

    def onDownloadChatToggled(self, enabled: bool) -> None:
        from Core import App
        if enabled:
            if App.Preferences.download.isCreateSubfolderForDownloadsEnabled():
                self._ui.createSubfolderForDownloadsCheckBox.setChecked(True)
        else:
            self._ui.createSubfolderForDownloadsCheckBox.setChecked(False)

    def getChannelFromText(self, text: str) -> str | None:
        parsedData = TwitchQueryParser.parseQuery(text)
        for mode, query in parsedData:
            if mode.isChannel():
                return query
        return None

    def accept(self) -> None:
        formCheck = []
        if self.virtualPreset.channel == "":
            formCheck.append(T("channel"))
        if self.virtualPreset.filenameTemplate == "":
            formCheck.append(T("filename-template"))
        if len(formCheck) != 0:
            formInfo = "\n".join(formCheck)
            Utils.info("warning", f"{T("messages.#some_fields_are_empty")}\n\n{formInfo}", contentTranslate=False, parent=self)
            return
        if not self.isEditMode:
            channel = self.getChannelFromText(self.virtualPreset.channel)
            if channel == None:
                Utils.info("error", "errors.#channel_id_is_invalid", parent=self)
                return
            else:
                self.virtualPreset.channel = channel
        self.savePreset()
        self.scheduledDownloadPreset.saveOptionHistory()
        self.scheduledDownloadUpdated.emit(self.scheduledDownloadPreset)
        super().accept()

    def changeEvent(self, event: QtCore.QEvent) -> None:
        super().changeEvent(event)
        if event.type() == QtCore.QEvent.Type.LanguageChange:
            self._ui.retranslateUi(self)
            self.retranslateDynamicUi()

    def retranslateDynamicUi(self) -> None:
        pass
