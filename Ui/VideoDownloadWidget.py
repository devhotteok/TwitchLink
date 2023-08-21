from Core.Ui import *
from Services.Twitch.GQL.TwitchGQLModels import Channel, Stream, Video, Clip
from Ui.Components.Utils.VideoWidgetImageSaver import VideoWidgetImageSaver
from Ui.Components.Widgets.DownloadButton import DownloadButton
from Ui.Components.Widgets.InstantDownloadButton import InstantDownloadButton


class VideoDownloadWidget(QtWidgets.QWidget):
    accountPageShowRequested = QtCore.pyqtSignal()

    def __init__(self, content: Channel | Stream | Video | Clip, resizable: bool = True, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.content = content
        self._ui = UiLoader.load("videoDownloadWidget", self)
        self._ui.videoWidget = Utils.setPlaceholder(self._ui.videoWidget, Ui.VideoWidget(self.content, resizable=resizable, parent=self))
        self.downloadButtonManager = DownloadButton(self.content, self._ui.downloadButton, buttonText=T("live-download" if isinstance(self.content, Channel) or isinstance(self.content, Stream) else "download"), parent=self)
        self.downloadButtonManager.accountPageShowRequested.connect(self.accountPageShowRequested)
        self.instantDownloadButtonManager = InstantDownloadButton(self.content, self._ui.instantDownloadButton, parent=self)
        self.instantDownloadButtonManager.accountPageShowRequested.connect(self.accountPageShowRequested)
        self._contextMenu = QtWidgets.QMenu(parent=self)
        self._filePropertyAction = QtGui.QAction(QtGui.QIcon(Icons.FILE_ICON), T("view-file-properties"), parent=self._contextMenu)
        self._imagePropertyAction = QtGui.QAction(QtGui.QIcon(Icons.IMAGE_ICON), T("view-image-properties"), parent=self._contextMenu)
        self._saveImageAction = QtGui.QAction(QtGui.QIcon(Icons.SAVE_ICON), T("save-image"), parent=self._contextMenu)
        self._filePropertyAction.triggered.connect(self.showFileProperty)
        self._imagePropertyAction.triggered.connect(self.showImageProperty)
        self._saveImageAction.triggered.connect(self.saveImage)
        if isinstance(self.content, Channel):
            self._filePropertyAction.setVisible(False)
            self._imagePropertyAction.setVisible(False)
        if self._ui.videoWidget.thumbnailImage.getImageUrl() == "":
            self._saveImageAction.setVisible(False)
        self.customContextMenuRequested.connect(self.contextMenuRequested)
        self._ui.videoWidget.thumbnailImage.customContextMenuRequested.connect(self.thumbnailImageContextMenuRequested)

    def setThumbnailImageStyleSheet(self, styleSheet: str) -> None:
        self._ui.videoWidget.thumbnailImage.setStyleSheet(styleSheet)

    def contextMenuRequested(self, position: QtCore.QPoint) -> None:
        self.showContextMenu((self._filePropertyAction,), position)

    def thumbnailImageContextMenuRequested(self, position: QtCore.QPoint) -> None:
        self.showContextMenu((self._filePropertyAction, self._imagePropertyAction, self._saveImageAction), position)

    def showContextMenu(self, actions: tuple[QtGui.QAction, ...], position: QtCore.QPoint) -> None:
        if any(action.isVisible() for action in actions):
            self._contextMenu.exec(actions, self.mapToGlobal(position))

    def showFileProperty(self) -> None:
        self._ui.videoWidget.showProperty(index=0)

    def showImageProperty(self) -> None:
        self._ui.videoWidget.showProperty(index=1)

    def saveImage(self) -> None:
        VideoWidgetImageSaver.saveImage(self.content, self._ui.videoWidget.thumbnailImage.pixmap(), parent=self)