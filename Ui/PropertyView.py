from Core.Ui import *
from Ui.Components.Utils.VideoWidgetImageSaver import VideoWidgetImageSaver


class PropertyView(QtWidgets.QDialog, WindowGeometryManager):
    def __init__(self, windowTitle: str, targetVideoWidget: Ui.VideoWidget, formData: dict, enableLabelTranslation: bool = False, enableLabelSelection: bool = False, enableFieldTranslation: bool = False, enableFieldSelection: bool = False, pageIndex: int = 0, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.targetVideoWidget = targetVideoWidget
        self._ui = UiLoader.load("propertyView", self)
        self.setWindowTitle(windowTitle)
        self.formData = formData
        self.enableLabelTranslation = enableLabelTranslation
        self.enableLabelSelection = enableLabelSelection
        self.enableFieldTranslation = enableFieldTranslation
        self.enableFieldSelection = enableFieldSelection
        if self.targetVideoWidget == None:
            self._ui.tabWidget.setTabVisible(1, False)
            self._ui.videoWidget.hide()
            self._ui.line_1.hide()
        else:
            self.setWindowFlag(QtCore.Qt.WindowType.WindowMaximizeButtonHint)
            self.loadWindowGeometry()
            self.finished.connect(self.saveWindowGeometry)
            self._ui.videoWidget = Utils.setPlaceholder(self._ui.videoWidget, Ui.VideoWidget(self.targetVideoWidget.content, resizable=True, showMore=True, thumbnailSync=self.targetVideoWidget._ui.thumbnailImage, categorySync=self.targetVideoWidget._ui.categoryImage, parent=self))
            self.setPreviewTab()
        self.setFormData()
        self._ui.tabWidget.setCurrentIndex(pageIndex)

    def setFormData(self) -> None:
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
            self._ui.propertyViewArea.layout().addRow(key, value)
        self._ui.propertyViewArea.adjustSize()

    def setPreviewTab(self) -> None:
        self._ui.previewImage.setImageSizePolicy(QtCore.QSize(384, 216), QtCore.QSize(1920, 1080))
        self._ui.previewImage.syncImage(self.targetVideoWidget._ui.thumbnailImage)
        self.embedUrl = self.targetVideoWidget._ui.thumbnailImage.getImageUrl()
        if self.embedUrl == "":
            self._ui.saveImageButton.setEnabled(False)
            self._ui.urlArea.setEnabled(False)
        else:
            self._ui.saveImageButton.clicked.connect(self.saveImage)
            self._ui.urlData.setText(self.embedUrl)
            self._ui.urlData.setToolTip(self.embedUrl)
            self._ui.copyUrlButton.clicked.connect(self.copyUrl)
            self._ui.openUrlButton.clicked.connect(self.openUrl)

    def saveImage(self) -> None:
        VideoWidgetImageSaver.saveImage(self.targetVideoWidget.content, self.targetVideoWidget.thumbnailImage.pixmap(), parent=self)

    def copyUrl(self) -> None:
        Utils.copyToClipboard(self.embedUrl)
        Utils.info("notification", "#Copied to clipboard.", parent=self)

    def openUrl(self) -> None:
        Utils.openUrl(self.embedUrl)