from Core.Ui import *
from Download.DownloadManager import DownloadManager


class PreviewWidgetItem(QtWidgets.QListWidgetItem):
    def __init__(self, downloaderId, parent=None):
        super(PreviewWidgetItem, self).__init__(parent=parent)
        self.widget = Ui.DownloadPreview(downloaderId, parent=parent)
        self.widget.setContentsMargins(10, 10, 10, 10)
        self.setSizeHint(self.widget.sizeHint())

class Downloads(QtWidgets.QWidget, UiFile.downloads):
    progressWindowRequested = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(Downloads, self).__init__(parent=parent)
        self.previewItems = {}
        self.typeFilter.currentIndexChanged.connect(self.updateFilter)
        self.statusFilter.currentIndexChanged.connect(self.updateFilter)
        self.updateFilter()
        self.previewWidgetView.itemSelectionChanged.connect(self.removeSelection)
        self.previewWidgetView.itemClicked.connect(self.openProgressWindow)
        self.previewWidgetView.verticalScrollBar().setSingleStep(30)
        self.showPreviewCount()
        self.downloadCompleteActionInfo.clicked.connect(self.showDownloadCompleteActionInfo)

    def downloaderCreated(self, downloaderId):
        item = PreviewWidgetItem(downloaderId=downloaderId)
        self.previewItems[downloaderId] = item
        self.previewWidgetView.setMinimumWidth(item.sizeHint().width() + self.previewWidgetView.verticalScrollBar().sizeHint().width())
        self.previewWidgetView.insertItem(0, item)
        self.previewWidgetView.setItemWidget(item, item.widget)
        self.processPreview(downloaderId)

    def downloaderDestroyed(self, downloaderId):
        self.previewWidgetView.takeItem(self.previewWidgetView.row(self.previewItems.pop(downloaderId)))
        self.showPreviewCount()

    def downloadCompleted(self, downloaderId):
        self.processPreview(downloaderId)

    def processPreview(self, downloaderId):
        self.setPreviewHidden(downloaderId, not self.filterPreview(downloaderId))
        self.showPreviewCount()

    def setPreviewHidden(self, downloaderId, hidden):
        self.previewItems[downloaderId].setHidden(hidden)

    def showPreviewCount(self):
        self.totalCount.setText(len(self.previewItems))
        self.filteredCount.setText(self.getFilteredPreviewCount())

    def updateFilter(self):
        self.downloaderType = self.typeFilter.currentIndex()
        self.downloaderStatus = self.statusFilter.currentIndex()
        for downloaderId in self.previewItems:
            self.processPreview(downloaderId)

    def getFilteredPreviewCount(self):
        return sum(0 if item.isHidden() else 1 for item in self.previewItems.values())

    def filterPreview(self, downloaderId):
        downloader = DownloadManager.get(downloaderId)
        return self._filterType(downloader) and self._filterStatus(downloader)

    def _filterType(self, downloader):
        if self.downloaderType == 0:
            return True
        elif self.downloaderType == 1:
            return downloader.setup.downloadInfo.type.isStream()
        elif self.downloaderType == 2:
            return downloader.setup.downloadInfo.type.isVideo()
        else:
            return downloader.setup.downloadInfo.type.isClip()

    def _filterStatus(self, downloader):
        if self.downloaderStatus == 0:
            return True
        elif self.downloaderStatus == 1:
            return downloader.isRunning()
        elif self.downloaderStatus == 2:
            return downloader.isFinished()
        elif self.downloaderStatus == 3:
            return downloader.isFinished() and downloader.status.terminateState.isFalse()
        elif self.downloaderStatus == 4:
            return downloader.isFinished() and downloader.status.terminateState.isTrue() and downloader.status.getError() != None
        else:
            return downloader.isFinished() and downloader.status.terminateState.isTrue() and downloader.status.getError() == None

    def removeSelection(self):
        for item in self.previewWidgetView.selectedItems():
            item.setSelected(False)

    def openProgressWindow(self, item):
        if item.widget.isEnabled():
            self.progressWindowRequested.emit(item.widget.downloaderId)

    def showDownloadCompleteActionInfo(self):
        self.info("information", "#When all downloads are complete, it will perform the selected action.\nA warning notification will be displayed for a period of time so that the operation can be canceled.\nWhen the time expires, the action will be performed.")