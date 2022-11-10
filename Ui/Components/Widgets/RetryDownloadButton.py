from Core.Ui import *
from Search import ExternalPlaylist
from Download.DownloadManager import DownloadManager
from Ui.Components.Widgets.DownloadButton import DownloadButton


class RetryDownloadButton(DownloadButton):
    def __init__(self, downloadInfo, button, downloaderId=None, buttonText=None, parent=None):
        super(RetryDownloadButton, self).__init__(downloadInfo.videoData, button, buttonText, parent=parent)
        self.downloadInfo = downloadInfo
        self.downloaderId = downloaderId
        if isinstance(self.downloadInfo.accessToken, ExternalPlaylist.ExternalPlaylist):
            self.button.clicked.disconnect()
            self.button.clicked.connect(self.retryExternalContentDownload)

    def askDownloadThroughHistory(self, contentType, properties):
        return self.ask("warning", T("#Attempting to start a new download based on your download history.\nFile data and download settings are generated based on this history and may differ from the current {contentType}. ({properties}, etc.)", contentType=contentType, properties=", ".join(properties)), contentTranslate=False)

    def downloadStream(self):
        if self.askDownloadThroughHistory(T("stream"), (f"{T('file-type')}[{T('stream')}, {T('rerun')}]", T("id"), T("title"), T("started-at"), T("available-resolutions"))):
            super().downloadStream()

    def downloadVideo(self):
        if self.askDownloadThroughHistory(T("video"), (T("title"), T("duration"), T("views"), T("available-resolutions"))):
            super().downloadVideo()

    def downloadClip(self):
        if self.askDownloadThroughHistory(T("clip"), (T("title"), T("duration"), T("views"), T("available-resolutions"))):
            super().downloadClip()

    def generateDownloadInfo(self, accessToken):
        downloadInfo = self.downloadInfo.copy()
        downloadInfo.setAccessToken(accessToken)
        return downloadInfo

    def startDownload(self, downloadInfo):
        if self.downloaderId != None:
            DownloadManager.remove(self.downloaderId)
        super().startDownload(downloadInfo)

    def retryExternalContentDownload(self):
        self.askDownload(self.downloadInfo.copy())