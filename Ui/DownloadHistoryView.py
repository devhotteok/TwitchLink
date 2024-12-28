from Core.Ui import *
from Services.Messages import Messages
from Download.DownloadInfo import DownloadInfo
from Download.History.DownloadHistory import DownloadHistory
from Ui.Components.Widgets.RetryDownloadButton import RetryDownloadButton


class DownloadHistoryView(QtWidgets.QWidget):
    accountPageShowRequested = QtCore.pyqtSignal()

    def __init__(self, downloadHistory: DownloadHistory, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.downloadHistory = downloadHistory
        self._ui = UiLoader.load("downloadHistoryView", self)
        self._ui.downloadViewControlBar = Utils.setPlaceholder(self._ui.downloadViewControlBar, Ui.DownloadViewControlBar(parent=self))
        self._ui.downloadViewControlBar.showDownloadInfo(self.downloadInfo)
        self._retryButtonManager = RetryDownloadButton(
            downloadInfo=self.downloadInfo,
            button=self._ui.downloadViewControlBar.retryButton.button,
            parent=self
        )
        self._retryButtonManager.accountPageShowRequested.connect(self.accountPageShowRequested)
        self._ui.downloadViewControlBar.retryButton.setVisible()
        self._ui.downloadViewControlBar.openFolderButton.clicked.connect(self.openFolder)
        self._ui.downloadViewControlBar.openFolderButton.setVisible()
        self._ui.downloadViewControlBar.openFileButton.clicked.connect(self.openFile)
        self._ui.downloadViewControlBar.openLogsButton.clicked.connect(self.openLogs)
        self._ui.downloadViewControlBar.deleteButton.clicked.connect(self.deleteHistory)
        self._ui.downloadViewControlBar.deleteButton.setVisible()
        self._ui.downloadInfoView = Utils.setPlaceholder(self._ui.downloadInfoView, Ui.DownloadInfoView(parent=self))
        self._ui.downloadInfoView.showDownloadInfo(self.downloadInfo)
        self.downloadHistory.historyUpdated.connect(self.reloadHistoryData)
        self.reloadHistoryData()

    @property
    def downloadInfo(self) -> DownloadInfo:
        return self.downloadHistory.downloadInfo

    def reloadHistoryData(self) -> None:
        self._updateDurationInfo()
        self._ui.startedAt.setText(self.downloadHistory.startedAt)
        self._ui.completedAt.setText(T("unknown") if self.downloadHistory.completedAt == None else self.downloadHistory.completedAt)
        self._ui.result.setText(T(self.downloadHistory.result) if self.downloadHistory.error == None else f"{T(self.downloadHistory.result)}\n({T(self.downloadHistory.error)})")
        if self.downloadHistory.result in (self.downloadHistory.Result.completed, self.downloadHistory.Result.stopped):
            self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
            self._ui.downloadViewControlBar.openFileButton.setVisible()
            self._ui.downloadViewControlBar.openLogsButton.setVisible()
        else:
            self.setCursor(QtCore.Qt.CursorShape.ArrowCursor)
            if self.downloadHistory.result == self.downloadHistory.Result.downloading:
                self._ui.downloadViewControlBar.openFileButton.setDownloading()
                self._ui.downloadViewControlBar.openLogsButton.setCreating()
            else:
                self._ui.historyInfoArea.setStyleSheet("QLabel {color: #ff0000;}")
                self._ui.downloadViewControlBar.openFileButton.setFileNotFound()
                self._ui.downloadViewControlBar.openLogsButton.setVisible()

    def _updateDurationInfo(self) -> None:
        if self.downloadInfo.type.isStream():
            self._ui.downloadInfoView.updateDurationInfo(self.downloadHistory.progressDetails.milliseconds)
        elif self.downloadInfo.type.isVideo():
            self._ui.downloadInfoView.updateDurationInfo(
                totalMilliseconds=int(self.downloadInfo.content.lengthSeconds * 1000),
                progressMilliseconds=self.downloadHistory.progressDetails.milliseconds,
                cropRangeMilliseconds=self.downloadInfo.getCropRangeMilliseconds()
            )
        elif self.downloadInfo.type.isClip():
            return
        self._ui.downloadInfoView.showMutedInfo(self.downloadHistory.progressDetails.mutedFiles, self.downloadHistory.progressDetails.mutedMilliseconds)
        self._ui.downloadInfoView.showSkippedInfo(self.downloadHistory.progressDetails.skippedFiles, self.downloadHistory.progressDetails.skippedMilliseconds)
        self._ui.downloadInfoView.showMissingInfo(self.downloadHistory.progressDetails.missingFiles, self.downloadHistory.progressDetails.missingMilliseconds)

    def deleteHistory(self) -> None:
        App.DownloadHistory.removeHistory(self.downloadHistory)

    def clickHandler(self) -> None:
        if self.downloadHistory.result in (self.downloadHistory.Result.completed, self.downloadHistory.Result.stopped):
            self.openFile()

    def openFolder(self) -> None:
        if not Utils.openFolder(self.downloadInfo.directory):
            Utils.info(*Messages.INFO.FOLDER_NOT_FOUND, parent=self)

    def openFile(self) -> None:
        if not Utils.openFile(self.downloadInfo.getAbsoluteFileName()):
            Utils.info(*Messages.INFO.FILE_NOT_FOUND, parent=self)

    def openLogs(self) -> None:
        if not Utils.openFile(self.downloadHistory.logFile):
            Utils.info(*Messages.INFO.FILE_NOT_FOUND, parent=self)