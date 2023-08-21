from Core.Ui import *
from Services.PartnerContent.PartnerContentInFeedWidgetListViewer import PartnerContentInFeedWidgetListViewer
from Download.Downloader.Core.BaseDownloader import BaseDownloader

import uuid


class Downloads(QtWidgets.QWidget):
    accountPageShowRequested = QtCore.pyqtSignal()
    progressWindowRequested = QtCore.pyqtSignal(object)
    downloadHistoryRequested = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._previewWidgets = {}
        self._ui = UiLoader.load("downloads", self)
        self._ui.typeFilter.currentIndexChanged.connect(self.updateFilter)
        self._ui.statusFilter.currentIndexChanged.connect(self.updateFilter)
        self.updateFilter()
        self._ui.infoIcon = Utils.setSvgIcon(self._ui.infoIcon, Icons.STORAGE_ICON)
        self._ui.stackedWidget.setStyleSheet(f"#stackedWidget {{background-color: {self._ui.stackedWidget.palette().color(QtGui.QPalette.ColorGroup.Normal, QtGui.QPalette.ColorRole.Base).name()};}}")
        self._widgetListViewer = PartnerContentInFeedWidgetListViewer(self._ui.previewWidgetView, partnerContentSize=QtCore.QSize(320, 100), parent=self)
        self._widgetListViewer.widgetClicked.connect(self.openProgressWindow)
        self.showStats()
        self._ui.downloadHistoryButton.clicked.connect(self.downloadHistoryRequested)
        self._ui.scheduledShutdownInfo.clicked.connect(self.showScheduledShutdownInfo)

    def downloaderCreated(self, downloaderId: uuid.UUID) -> None:
        widget = Ui.DownloadPreview(downloaderId, parent=None)
        widget.accountPageShowRequested.connect(self.accountPageShowRequested)
        self._widgetListViewer.insertWidget(0, widget, resizeSignal=widget.resizedSignal)
        self._previewWidgets[downloaderId] = widget
        self.processPreview(downloaderId)

    def downloaderDestroyed(self, downloaderId: uuid.UUID) -> None:
        self._widgetListViewer.removeWidget(self._previewWidgets.pop(downloaderId))
        self.showStats()

    def downloadStarted(self, downloaderId: uuid.UUID) -> None:
        self.processPreview(downloaderId)

    def downloadCompleted(self, downloaderId: uuid.UUID) -> None:
        self.processPreview(downloaderId)

    def processPreview(self, downloaderId: uuid.UUID) -> None:
        self.setPreviewHidden(downloaderId, not self.filterPreview(downloaderId))
        self.showStats()

    def setPreviewHidden(self, downloaderId: uuid.UUID, hidden: bool) -> None:
        self._previewWidgets[downloaderId].setHidden(hidden)

    def getPreviewCount(self) -> int:
        return len(self._previewWidgets)

    def showStats(self) -> None:
        self._ui.totalCount.setText(self.getPreviewCount())
        previewCount = self.getFilteredPreviewCount()
        self._ui.filteredCount.setText(previewCount)
        if previewCount == 0:
            self._ui.infoLabel.setText(T("#Your downloads will be displayed here." if self.downloaderType == 0 and self.downloaderStatus == 0 else "#There are no matches for this filter."))
            self._ui.stackedWidget.setCurrentIndex(0)
        else:
            self._ui.stackedWidget.setCurrentIndex(1)

    def updateFilter(self) -> None:
        self.downloaderType = self._ui.typeFilter.currentIndex()
        self.downloaderStatus = self._ui.statusFilter.currentIndex()
        for downloaderId in self._previewWidgets:
            self.setPreviewHidden(downloaderId, not self.filterPreview(downloaderId))
        self.showStats()

    def getFilteredPreviewCount(self) -> int:
        return sum(0 if item.isHidden() else 1 for item in self._previewWidgets.values())

    def filterPreview(self, downloaderId: uuid.UUID) -> bool:
        downloader = App.DownloadManager.get(downloaderId)
        return self._filterType(downloader) and self._filterStatus(downloader)

    def _filterType(self, downloader: BaseDownloader) -> bool:
        if self.downloaderType == 0:
            return True
        elif self.downloaderType == 1:
            return downloader.downloadInfo.type.isStream()
        elif self.downloaderType == 2:
            return downloader.downloadInfo.type.isVideo()
        else:
            return downloader.downloadInfo.type.isClip()

    def _filterStatus(self, downloader: BaseDownloader) -> bool:
        if self.downloaderStatus == 0:
            return True
        elif self.downloaderStatus == 1:
            return downloader.isRunning()
        elif self.downloaderStatus == 2:
            return downloader.isFinished()
        elif self.downloaderStatus == 3:
            return downloader.isFinished() and downloader.status.terminateState.isFalse()
        elif self.downloaderStatus == 4:
            return downloader.isFinished() and downloader.status.terminateState.isTrue() and not isinstance(downloader.status.getError(), Exceptions.AbortRequested)
        else:
            return downloader.isFinished() and downloader.status.terminateState.isTrue() and isinstance(downloader.status.getError(), Exceptions.AbortRequested)

    def openProgressWindow(self, widget: Ui.DownloadPreview) -> None:
        if widget.isEnabled():
            self.progressWindowRequested.emit(widget.downloaderId)

    def showScheduledShutdownInfo(self) -> None:
        Utils.info("information", "#When all downloads are complete, it will perform the selected action.\nA warning notification will be displayed for a period of time so that the operation can be canceled.\nWhen the time expires, the action will be performed.", parent=self)