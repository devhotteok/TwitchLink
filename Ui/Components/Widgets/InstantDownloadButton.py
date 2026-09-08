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
            absoluteFileName = Utils.createUniqueFile(downloadInfo.directory, downloadInfo.fileName, downloadInfo.fileFormat, exclude=FileNameLocker.getLockedFiles())
            downloadInfo.setAbsoluteFileName(absoluteFileName)
            if downloadInfo.isCreateSubfolderForDownloadsEnabled():
                import os
                if os.path.exists(absoluteFileName) and os.path.getsize(absoluteFileName) == 0:
                    os.remove(absoluteFileName)
        except:
            self.info("error", "errors.#an_error_occurred_while_generating_file")
            super().askDownload(downloadInfo)
        else:
            downloadInfo.saveOptionHistory()
            self.startDownload(downloadInfo)