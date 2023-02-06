from Core.Ui import *
from Download.ScheduledDownloadManager import ScheduledDownloadManager
from Ui.Components.Operators.TabManager import TabManager


class ScheduledDownloadsPage(TabManager):
    def __init__(self, pageObject, parent=None):
        super(ScheduledDownloadsPage, self).__init__(parent=parent)
        self.pageObject = pageObject
        self.scheduledDownloads = Ui.ScheduledDownloads(parent=self)
        self.addTab(self.scheduledDownloads, icon=Icons.FOLDER_ICON, closable=False)
        ScheduledDownloadManager.downloaderCountChangedSignal.connect(self.changePageText)

    def changePageText(self, downloadersCount):
        self.pageObject.setPageName("" if downloadersCount == 0 else str(downloadersCount))