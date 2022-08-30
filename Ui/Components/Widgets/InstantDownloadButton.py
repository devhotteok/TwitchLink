from Ui.Components.Widgets.DownloadButton import DownloadButton
from Ui.Components.Utils.DownloadChecker import DownloadChecker


class InstantDownloadButton(DownloadButton):
    def __init__(self, videoData, button, buttonText=None, parent=None):
        super(InstantDownloadButton, self).__init__(videoData, button, buttonText, parent=parent)

    def askDownload(self, downloadInfo):
        downloadAvailableState = DownloadChecker.isDownloadAvailable(downloadInfo, parent=self.button)
        if downloadAvailableState == DownloadChecker.State.AVAILABLE:
            downloadInfo.saveOptionHistory()
            self.startDownload(downloadInfo)
        elif downloadAvailableState == DownloadChecker.State.NEED_NEW_FILE_NAME:
            super().askDownload(downloadInfo)