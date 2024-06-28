from Core.Ui import *
from Services.Twitch.Playback import TwitchPlaybackModels
from Search import ExternalPlaybackGenerator
from Download.DownloadInfo import DownloadInfo
from Ui.Components.Widgets.DownloadButton import DownloadButton

import uuid


class RetryDownloadButton(DownloadButton):
    def __init__(self, downloadInfo: DownloadInfo, button: QtWidgets.QPushButton | QtWidgets.QToolButton, buttonIcon: ThemedIcon | None = None, buttonText: str | None = None, downloaderId: uuid.UUID | None = None, parent: QtCore.QObject | None = None):
        super().__init__(downloadInfo.content, button, buttonIcon, buttonText, parent=parent)
        self.downloadInfo = downloadInfo
        self.downloaderId = downloaderId
        if isinstance(self.downloadInfo.playback, ExternalPlaybackGenerator.ExternalPlayback):
            self.button.clicked.disconnect()
            self.button.clicked.connect(self.retryExternalContentDownload)

    def askDownloadThroughHistory(self, contentType: str, properties: tuple[str, ...]) -> bool:
        return self.ask("warning", T("#Attempting to start a new download based on your download history.\nFile data and download settings are generated based on this history and may differ from the current {contentType}. ({properties}, etc.)", contentType=contentType, properties=", ".join(properties)), contentTranslate=False)

    def downloadStream(self) -> None:
        if self.askDownloadThroughHistory(T("stream"), (f"{T('file-type')}[{T('stream')}, {T('rerun')}]", T("id"), T("title"), T("started-at"), T("available-resolutions"))):
            super().downloadStream()

    def downloadVideo(self) -> None:
        if self.askDownloadThroughHistory(T("video"), (T("title"), T("duration"), T("views"), T("available-resolutions"))):
            super().downloadVideo()

    def downloadClip(self) -> None:
        if self.askDownloadThroughHistory(T("clip"), (T("title"), T("duration"), T("views"), T("available-resolutions"))):
            super().downloadClip()

    def generateDownloadInfo(self, playback: TwitchPlaybackModels.TwitchStreamPlayback | TwitchPlaybackModels.TwitchVideoPlayback | TwitchPlaybackModels.TwitchClipPlayback) -> DownloadInfo:
        downloadInfo = self.downloadInfo.copy()
        downloadInfo.updatePlayback(playback)
        return downloadInfo

    def startDownload(self, downloadInfo: DownloadInfo) -> None:
        if self.downloaderId != None:
            App.DownloadManager.remove(self.downloaderId)
        super().startDownload(downloadInfo)

    def retryExternalContentDownload(self) -> None:
        self.askDownload(self.downloadInfo.copy())