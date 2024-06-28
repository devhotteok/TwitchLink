from Core.Ui import *
from Services.Theme.ThemedIcon import ThemedIcon
from Services.Twitch.GQL.TwitchGQLModels import Channel, Stream, Video, Clip
from Search import ExternalPlaybackGenerator
from Download.DownloadInfo import DownloadInfo

import enum


class DownloadViewControlButtonTypes(enum.Enum):
    Hidden = 0
    Visible = 1
    Disabled = 2
    Creating = 3
    Downloading = 4
    FileNotFound = 5

class DownloadViewControlButton:
    def __init__(self, button: QtWidgets.QPushButton, icon: ThemedIcon | None = None):
        self.button = button
        self.defaultIcon = icon
        self._buttonIconViewer = Utils.setIconViewer(self.button, icon)
        self._toolTip = self.button.toolTip()
        self.setHidden()

    @property
    def clicked(self) -> QtCore.pyqtSignal:
        return self.button.clicked

    def set(self, type: DownloadViewControlButtonTypes) -> None:
        if type == DownloadViewControlButtonTypes.Hidden:
            self.button.hide()
        else:
            if type == DownloadViewControlButtonTypes.Visible:
                self.button.setEnabled(True)
                self._buttonIconViewer.setIcon(self.defaultIcon)
                self.button.setToolTip(self._toolTip)
            elif type == DownloadViewControlButtonTypes.Disabled:
                self.button.setEnabled(False)
                self._buttonIconViewer.setIcon(self.defaultIcon)
                self.button.setToolTip(self._toolTip)
            elif type == DownloadViewControlButtonTypes.Creating:
                self.button.setEnabled(False)
                self._buttonIconViewer.setIcon(Icons.CREATING_FILE)
                self.button.setToolTip(f"{self._toolTip} ({T('creating', ellipsis=True)})")
            elif type == DownloadViewControlButtonTypes.Downloading:
                self.button.setEnabled(False)
                self._buttonIconViewer.setIcon(Icons.DOWNLOADING_FILE)
                self.button.setToolTip(f"{self._toolTip} ({T('downloading', ellipsis=True)})")
            elif type == DownloadViewControlButtonTypes.FileNotFound:
                self.button.setEnabled(False)
                self._buttonIconViewer.setIcon(Icons.FILE_NOT_FOUND)
                self.button.setToolTip(f"{self._toolTip} ({T('file-not-found')})")
            self.button.show()

    def setHidden(self) -> None:
        self.set(DownloadViewControlButtonTypes.Hidden)

    def setVisible(self) -> None:
        self.set(DownloadViewControlButtonTypes.Visible)

    def setDisabled(self) -> None:
        self.set(DownloadViewControlButtonTypes.Disabled)

    def setCreating(self) -> None:
        self.set(DownloadViewControlButtonTypes.Creating)

    def setDownloading(self) -> None:
        self.set(DownloadViewControlButtonTypes.Downloading)

    def setFileNotFound(self) -> None:
        self.set(DownloadViewControlButtonTypes.FileNotFound)


class DownloadViewControlBar(QtWidgets.QWidget):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("downloadViewControlBar", self)
        self._ui.viewIcon = Utils.setSvgIcon(self._ui.viewIcon, Icons.VIEWER)
        self.adsInfoButton = DownloadViewControlButton(self._ui.adsInfoButton, icon=Icons.WARNING_RED)
        self.adsInfoButton.clicked.connect(self._showAdsInfo)
        self.retryButton = DownloadViewControlButton(self._ui.retryButton, icon=Icons.RETRY)
        self.openFolderButton = DownloadViewControlButton(self._ui.openFolderButton, icon=Icons.FOLDER)
        self.openFileButton = DownloadViewControlButton(self._ui.openFileButton, icon=Icons.FILE)
        self.openLogsButton = DownloadViewControlButton(self._ui.openLogsButton, icon=Icons.TEXT_FILE)
        self.deleteButton = DownloadViewControlButton(self._ui.deleteButton, icon=Icons.TRASH)
        self.closeButton = DownloadViewControlButton(self._ui.closeButton, icon=Icons.CLOSE)

    def showContentInfo(self, content: Channel | Stream | Video | Clip) -> None:
        if isinstance(content, Channel):
            contentType = "offline"
            self._ui.viewerCountArea.hide()
            channel = content.displayName
        elif isinstance(content, Stream):
            contentType = "stream" if content.isLive() else "rerun"
            channel = content.broadcaster.displayName
            self._ui.viewerCount.setText(content.viewersCount)
            self._ui.viewerCountArea.show()
        elif isinstance(content, Video):
            contentType = "video"
            channel = content.owner.displayName
            self._ui.viewerCountArea.hide()
        else:
            contentType = "clip"
            channel = content.broadcaster.displayName
            self._ui.viewerCountArea.hide()
        self._ui.contentType.setText(T(contentType))
        self._ui.channel.setText(channel)
        self.adsInfoButton.setHidden()

    def showDownloadInfo(self, downloadInfo: DownloadInfo) -> None:
        self.showContentInfo(downloadInfo.content)
        if downloadInfo.type.isStream():
            contentType = "stream" if downloadInfo.content.isLive() else "rerun"
            if downloadInfo.playback.token.hideAds:
                self.adsInfoButton.setHidden()
            else:
                self.adsInfoButton.setVisible()
        elif downloadInfo.type.isVideo():
            contentType = "video"
            self.adsInfoButton.setHidden()
        else:
            contentType = "clip"
            self.adsInfoButton.setHidden()
        self._ui.contentType.setText(f"{T('external-content')} / {T(contentType)}" if isinstance(downloadInfo.playback, ExternalPlaybackGenerator.ExternalPlayback) else T(contentType))

    def _showAdsInfo(self) -> None:
        adsInfo = T("#This stream may contain ads.\nIf commercials are broadcast, the portion of the stream during the commercials may not be available for download, and it may appear as though the stream is interrupted.\nTo prevent ads, you need to log in with an account that has ad-free benefits, such as Twitch Turbo, or an account that subscribes to the channel.")
        changesInfo = T("#Changes will take effect from the next download.")
        Utils.info("warning", f"{adsInfo}\n\n{changesInfo}", contentTranslate=False, parent=self)