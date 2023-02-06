from Services.Utils.Utils import Utils
from Services.Translator.Translator import T
from Download.GlobalDownloadManager import GlobalDownloadManager


class DownloadChecker:
    class State:
        AVAILABLE = 0
        NEED_NEW_FILE_NAME = 1
        USER_REJECTED = 2


    @staticmethod
    def isFileNameDuplicate(fileName):
        for downloader in GlobalDownloadManager.getRunningDownloaders():
            if downloader.setup.downloadInfo.getAbsoluteFileName() == fileName:
                return True
        return False

    @classmethod
    def checkNetworkInstability(cls, downloadInfo, parent=None):
        if downloadInfo.type.isStream():
            if GlobalDownloadManager.isDownloaderRunning():
                return cls.warnNetworkInstability("download", "live", parent=parent)
        else:
            for downloader in GlobalDownloadManager.getRunningDownloaders():
                if downloader.setup.downloadInfo.type.isStream():
                    return cls.warnNetworkInstability("live-download", downloadInfo.type.toString(), parent=parent)
        return True

    @classmethod
    def warnNetworkInstability(self, downloadType, operationType, parent=None):
        return Utils.ask("warning", T("#You already have one or more {downloadType}s in progress.\nDepending on the network specifications, if you proceed with the {operationType} download, the live download may become unstable or interrupted.\nProceed?", downloadType=T(downloadType), operationType=T(operationType)), contentTranslate=False, parent=parent)

    @classmethod
    def isDownloadAvailable(cls, downloadInfo, parent=None):
        if cls.isFileNameDuplicate(downloadInfo.getAbsoluteFileName()):
            Utils.info("error", "#There is another download in progress with the same file name.", parent=parent)
            return cls.State.NEED_NEW_FILE_NAME
        elif Utils.isFile(downloadInfo.getAbsoluteFileName()):
            if not Utils.ask("overwrite", "#A file with the same name already exists.\nOverwrite?", parent=parent):
                return cls.State.USER_REJECTED
        elif not Utils.isDirectory(downloadInfo.directory) or Utils.isDirectory(downloadInfo.getAbsoluteFileName()):
            Utils.info("error", "#The target directory or filename is unavailable.", parent=parent)
            return cls.State.NEED_NEW_FILE_NAME
        if not cls.checkNetworkInstability(downloadInfo, parent=parent):
            return cls.State.USER_REJECTED
        return cls.State.AVAILABLE