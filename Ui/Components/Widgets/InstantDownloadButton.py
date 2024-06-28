from Core.Ui import *
from Services.FileNameLocker import FileNameLocker
from Services.Twitch.GQL import TwitchGQLModels
from Download.DownloadInfo import DownloadInfo
from Ui.Components.Widgets.DownloadButton import DownloadButton


class InstantDownloadButton(DownloadButton):
    def __init__(self, content: TwitchGQLModels.Channel | TwitchGQLModels.Stream | TwitchGQLModels.Video | TwitchGQLModels.Clip, button: QtWidgets.QPushButton | QtWidgets.QToolButton, buttonIcon: ThemedIcon | None = None, buttonText: str | None = None, parent: QtCore.QObject | None = None):
        super().__init__(content, button, buttonIcon, buttonText, parent=parent)

    def showStreamAdWarning(self) -> bool:
        return True

    def askDownload(self, downloadInfo: DownloadInfo) -> None:
        try:
            downloadInfo.setAbsoluteFileName(Utils.createUniqueFile(downloadInfo.directory, downloadInfo.fileName, downloadInfo.fileFormat, exclude=FileNameLocker.getLockedFiles()))
        except:
            self.info("error", "#An error occurred while generating the file name.")
            super().askDownload(downloadInfo)
        else:
            downloadInfo.saveOptionHistory()
            self.startDownload(downloadInfo)