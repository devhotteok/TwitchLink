from Core.Ui import *
from Services.Messages import Messages
from Services.Image.Config import Config as ImageConfig


class PropertyView(QtWidgets.QDialog, UiFile.propertyView, WindowGeometryManager):
    def __init__(self, windowTitle, targetVideoWidget, formData, enableLabelTranslation=False, enableLabelSelection=False, enableFieldTranslation=False, enableFieldSelection=False, parent=None):
        super(PropertyView, self).__init__(parent=parent)
        self.setWindowTitle(windowTitle)
        self.targetVideoWidget = targetVideoWidget
        self.formData = formData
        self.enableLabelTranslation = enableLabelTranslation
        self.enableLabelSelection = enableLabelSelection
        self.enableFieldTranslation = enableFieldTranslation
        self.enableFieldSelection = enableFieldSelection
        if self.targetVideoWidget == None:
            self.tabWidget.setTabVisible(1, False)
            self.videoWidget.hide()
            self.line.hide()
        else:
            self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint)
            self.loadWindowGeometry()
            self.finished.connect(self.saveWindowGeometry)
            self.videoWidget = Utils.setPlaceholder(self.videoWidget, Ui.VideoWidget(self.targetVideoWidget.data, resizable=True, viewOnly=True, thumbnailSync=self.targetVideoWidget.thumbnail_image, categorySync=self.targetVideoWidget.category_image, parent=self))
            self.setPreviewTab()
        self.setFormData()

    def setFormData(self):
        for key, value in self.formData.items():
            if not isinstance(key, QtCore.QObject):
                if isinstance(key, str):
                    if self.enableLabelTranslation:
                        key = T(key)
                    if self.targetVideoWidget != None:
                        key = f"{key}:"
                label = QtWidgets.QLabel(parent=self)
                label.setText(key)
                key = label
            if not isinstance(value, QtCore.QObject):
                if isinstance(value, str):
                    if self.enableFieldTranslation:
                        value = T(value)
                label = QtWidgets.QLabel(parent=self)
                label.setText(value)
                value = label
                if self.targetVideoWidget != None:
                    value.setSizePolicy(QtWidgets.QSizePolicy.Ignored, QtWidgets.QSizePolicy.Preferred)
            if self.enableLabelSelection and type(key) == QtWidgets.QLabel:
                key.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
            if self.enableFieldSelection and type(value) == QtWidgets.QLabel:
                value.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse | QtCore.Qt.TextSelectableByKeyboard)
            self.propertyViewArea.layout().addRow(key, value)
        self.propertyViewArea.adjustSize()

    def setPreviewTab(self):
        self.preview_image.setImageSizePolicy((384, 216), (1920, 1080))
        self.preview_image.syncImage(self.targetVideoWidget.thumbnail_image)
        self.embedUrl = self.targetVideoWidget.thumbnail_image.getImageUrl()
        if self.embedUrl == "":
            self.saveImageButton.setEnabled(False)
            self.urlArea.setEnabled(False)
        else:
            self.saveImageButton.clicked.connect(self.saveImage)
            self.urlData.setText(self.embedUrl)
            self.copyUrlButton.clicked.connect(self.copyUrl)
            self.openUrlButton.clicked.connect(self.openUrl)

    def saveImage(self):
        history = DB.temp.getDownloadHistory(ImageConfig.DATA_TYPE)
        directory = history.getUpdatedDirectory()
        filters = history.getAvailableFormats()
        initialFilter = history.getFormat()
        fileName = Utils.askSaveDirectory(Utils.joinPath(directory, self.createFileName()), filters, initialFilter, parent=self)
        if fileName != None:
            try:
                self.targetVideoWidget.thumbnail_image.pixmap().save(fileName)
            except:
                self.info(*Messages.INFO.FILE_SYSTEM_ERROR)
            else:
                history.setAbsoluteFileName(fileName)
                if self.ask(
                    "save-complete",
                    f"{T('#Save completed.')}\n\n{fileName}",
                    contentTranslate=False,
                    okText="open",
                    cancelText="ok"
                ):
                    try:
                        Utils.openFile(fileName)
                    except:
                        self.info(*Messages.INFO.FILE_NOT_FOUND)

    def createFileName(self):
        return Utils.getValidFileName(
            "[{type} {preview}] [{channel}] {id}".format(
                type=self.formData["file-type"],
                preview=T("preview"),
                channel=self.formData["channel"],
                id=self.targetVideoWidget.data.id
            )
        )

    def copyUrl(self):
        Utils.copyToClipboard(self.embedUrl)
        self.info("notification", "#Copied to clipboard.")

    def openUrl(self):
        Utils.openUrl(self.embedUrl)