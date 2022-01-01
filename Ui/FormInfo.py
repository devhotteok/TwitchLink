from Core.App import App
from Core.Ui import *
from Services.Messages import Messages
from Services.Utils.Image.Config import Config as ImageLoaderConfig

from os import path


class FormInfo(QtWidgets.QDialog, UiFile.formInfo):
    def __init__(self, windowTitle, videoData, formData, enableLabelTranslation=False, enableLabelSelection=False, enableFieldTranslation=False, enableFieldSelection=False):
        super().__init__(parent=App.getActiveWindow(), useWindowGeometry=False)
        self.setWindowTitle(windowTitle)
        self.videoData = videoData
        self.formData = formData
        self.enableLabelTranslation = enableLabelTranslation
        self.enableLabelSelection = enableLabelSelection
        self.enableFieldTranslation = enableFieldTranslation
        self.enableFieldSelection = enableFieldSelection
        if self.videoData == None:
            self.tabWidget.setTabVisible(1, False)
            self.videoWidgetPlaceholder.hide()
            self.line.hide()
        else:
            self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint)
            Utils.setPlaceholder(self.videoWidgetPlaceholder, Ui.VideoWidget(self.videoData, resizable=True, showMore=False))
            self.setPreviewTab()
        self.setFormData()
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)

    def setFormData(self):
        for key, value in self.formData.items():
            if not isinstance(key, QtCore.QObject):
                key = QtWidgets.QLabel(T(str(key)) if self.enableLabelTranslation else str(key))
                if self.videoData != None:
                    key.setText("{}:".format(key.text()))
            if not isinstance(value, QtCore.QObject):
                value = QtWidgets.QLabel(T(str(value)) if self.enableFieldTranslation else str(value))
                if self.videoData != None:
                    value.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
            if self.enableLabelSelection and type(key) == QtWidgets.QLabel:
                key.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
            if self.enableFieldSelection and type(value) == QtWidgets.QLabel:
                value.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
            self.formInfoArea.layout().addRow(key, value)

    def setPreviewTab(self):
        self.previewWidget = Ui.VideoWidget(self.videoData, resizable=True, previewOnly=True)
        Utils.setPlaceholder(self.previewVideoWidgetPlaceholder, self.previewWidget)
        self.saveImageButton.clicked.connect(self.saveImage)
        self.embedUrl = self.previewWidget.metaData["thumbnailImage"][0].format(width=1920, height=1080)
        if self.embedUrl == "":
            self.urlArea.setEnabled(False)
        else:
            self.urlData.setText(self.embedUrl)
            self.urlData.setCursorPosition(0)
            self.copyUrlButton.clicked.connect(self.copyUrl)
            self.openUrlButton.clicked.connect(self.openUrl)

    def saveImage(self):
        DB.temp.updateDefaultDirectory()
        directory = DB.temp.getDefaultDirectory()
        filters = self.getAvailableFormats()
        initialFilter = DB.temp.getDefaultFormat(ImageLoaderConfig.IMAGE_DATA_TYPE)
        fileName = Utils.askSaveDirectory(Utils.joinPath(directory, self.createFileName()), filters, initialFilter)
        if fileName != None:
            try:
                self.previewWidget.thumbnail_image.pixmap().save(fileName)
            except:
                Utils.info(*Messages.INFO.FILE_SYSTEM_ERROR)
            else:
                self.saveOptions(fileName)
                if Utils.ask(
                        "save-complete",
                        "{}\n\n{}".format(T("#Save completed."), fileName),
                        okText="open",
                        cancelText="ok"
                ):
                    try:
                        Utils.openFile(fileName)
                    except:
                        Utils.info(*Messages.INFO.FILE_NOT_FOUND)

    def createFileName(self):
        return Utils.getValidFileName(
            "[{type} {preview}] [{channel}] {id}".format(
                type=self.formData["file-type"],
                preview=T("preview"),
                channel=self.formData["channel"],
                id=self.videoData.id
            )
        )

    def getAvailableFormats(self):
        return ["jpg", "png"]

    def saveOptions(self, absoluteFileName):
        directory = path.dirname(absoluteFileName)
        fileFormat = path.basename(absoluteFileName).rsplit(".", 1)[1]
        DB.temp.setDefaultDirectory(directory)
        DB.temp.setDefaultFormat(ImageLoaderConfig.IMAGE_DATA_TYPE, fileFormat)

    def copyUrl(self):
        Utils.copyToClipboard(self.embedUrl)
        Utils.info("notification", "#Copied to clipboard.")

    def openUrl(self):
        Utils.openUrl(self.embedUrl)