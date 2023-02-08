from Services.Utils.Utils import Utils
from Services.FileNameManager import FileNameManager
from Ui.Components.Widgets.DownloadButton import DownloadButton


class InstantDownloadButton(DownloadButton):
    def __init__(self, videoData, button, buttonText=None, parent=None):
        super(InstantDownloadButton, self).__init__(videoData, button, buttonText, parent=parent)

    def askDownload(self, downloadInfo):
        try:
            downloadInfo.setAbsoluteFileName(Utils.createUniqueFile(downloadInfo.directory, downloadInfo.fileName, downloadInfo.fileFormat, exclude=FileNameManager.getLockedFileNames()))
        except:
            self.info("error", "#An error occurred while generating the file name.")
            super().askDownload(downloadInfo)
        else:
            downloadInfo.saveOptionHistory()
            self.startDownload(downloadInfo)