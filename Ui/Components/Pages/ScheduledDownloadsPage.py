from Core.Ui import *
from Ui.Components.Operators.NavigationBar import PageObject
from Ui.Components.Operators.TabManager import TabManager


class ScheduledDownloadsPage(TabManager):
    def __init__(self, pageObject: PageObject, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.pageObject = pageObject
        self.scheduledDownloads = Ui.ScheduledDownloads(parent=self)
        self.addTab(self.scheduledDownloads, icon=Icons.FOLDER_ICON, closable=False)
        App.ScheduledDownloadManager.downloaderCountChangedSignal.connect(self._changePageText)

    def _changePageText(self, downloadersCount: int) -> None:
        self.pageObject.setPageName("" if downloadersCount == 0 else str(downloadersCount))