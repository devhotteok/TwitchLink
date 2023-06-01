from Core.Ui import *
from Ui.Components.Utils.VideoWidgetImageSaver import VideoWidgetImageSaver


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
            self.line_1.hide()
        else:
            self.setWindowFlag(QtCore.Qt.WindowType.WindowMaximizeButtonHint)
            self.loadWindowGeometry()
            self.finished.connect(self.saveWindowGeometry)
            self.videoWidget = Utils.setPlaceholder(self.videoWidget, Ui.VideoWidget(self.targetVideoWidget.data, resizable=True, viewOnly=True, thumbnailSync=self.targetVideoWidget.thumbnailImage, categorySync=self.targetVideoWidget.categoryImage, parent=self))
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
                    value.setSizePolicy(QtWidgets.QSizePolicy.Policy.Ignored, QtWidgets.QSizePolicy.Policy.Preferred)
            if self.enableLabelSelection and type(key) == QtWidgets.QLabel:
                key.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse | QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard)
            if self.enableFieldSelection and type(value) == QtWidgets.QLabel:
                value.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByMouse | QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard)
            self.propertyViewArea.layout().addRow(key, value)
        self.propertyViewArea.adjustSize()

    def setPreviewTab(self):
        self.previewImage.setImageSizePolicy((384, 216), (1920, 1080))
        self.previewImage.syncImage(self.targetVideoWidget.thumbnailImage)
        self.embedUrl = self.targetVideoWidget.thumbnailImage.getImageUrl()
        if self.embedUrl == "":
            self.saveImageButton.setEnabled(False)
            self.urlArea.setEnabled(False)
        else:
            self.saveImageButton.clicked.connect(self.saveImage)
            self.urlData.setText(self.embedUrl)
            self.urlData.setToolTip(self.embedUrl)
            self.copyUrlButton.clicked.connect(self.copyUrl)
            self.openUrlButton.clicked.connect(self.openUrl)

    def saveImage(self):
        VideoWidgetImageSaver.saveImage(self, self.targetVideoWidget)

    def copyUrl(self):
        Utils.copyToClipboard(self.embedUrl)
        self.info("notification", "#Copied to clipboard.")

    def openUrl(self):
        Utils.openUrl(self.embedUrl)