from Core.Ui import *
from Services.Messages import Messages
from Download.Downloader.Core.StreamDownloader import StreamDownloader
from Download.Downloader.Core.VideoDownloader import VideoDownloader
from Download.Downloader.Core.ClipDownloader import ClipDownloader
from Ui.Components.Widgets.RetryDownloadButton import RetryDownloadButton
from Ui.Components.Widgets.WidgetRemoveController import WidgetRemoveController

import uuid


class DownloadPreview(QtWidgets.QWidget):
    resizedSignal = QtCore.pyqtSignal()
    accountPageShowRequested = QtCore.pyqtSignal()

    def __init__(self, downloaderId: uuid.UUID, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.downloaderId = downloaderId
        self._downloader: StreamDownloader | VideoDownloader | ClipDownloader | None = None
        self._widgetRemoveController = WidgetRemoveController(parent=self)
        self._widgetRemoveController.performRemove.connect(self.removeDownloader)
        self._ui = UiLoader.load("downloadPreview", self)
        self._ui.downloadViewControlBar = Utils.setPlaceholder(self._ui.downloadViewControlBar, Ui.DownloadViewControlBar(parent=self))
        self._ui.downloadViewControlBar.openFolderButton.clicked.connect(self.openFolder)
        self._ui.downloadViewControlBar.openFileButton.clicked.connect(self.openFile)
        self._ui.downloadViewControlBar.openLogsButton.clicked.connect(self.openLogs)
        self._ui.downloadViewControlBar.closeButton.clicked.connect(self.tryRemoveDownloader)
        self._ui.downloaderView = Utils.setPlaceholder(self._ui.downloaderView, Ui.DownloaderView(parent=self))
        self._ui.downloaderView.resizedSignal.connect(self.resizedSignal, QtCore.Qt.ConnectionType.QueuedConnection)
        self._ui.pauseButton.clicked.connect(self.pauseResume)
        self._ui.cancelButton.clicked.connect(self.cancel)
        self.connectDownloader(App.DownloadManager.get(self.downloaderId))

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        self.resizedSignal.emit()
        super().showEvent(event)

    def connectDownloader(self, downloader: StreamDownloader | VideoDownloader | ClipDownloader) -> None:
        self.disconnectDownloader()
        self._widgetRemoveController.setRemoveEnabled(False)
        self._downloader = downloader
        self._retryButtonManager = RetryDownloadButton(
            downloadInfo=self._downloader.downloadInfo,
            button=self._ui.downloadViewControlBar.retryButton.button,
            downloaderId=self.downloaderId,
            parent=self
        )
        self._retryButtonManager.accountPageShowRequested.connect(self.accountPageShowRequested)
        self._ui.downloadViewControlBar.showDownloadInfo(self._downloader.downloadInfo)
        self._ui.downloadViewControlBar.retryButton.setHidden()
        self._ui.downloadViewControlBar.openFolderButton.setVisible()
        self._ui.downloadViewControlBar.openFileButton.setDownloading()
        self._ui.downloadViewControlBar.openLogsButton.setCreating()
        self._ui.downloadViewControlBar.closeButton.setVisible()
        self._ui.downloaderView.connectDownloader(self._downloader)
        if isinstance(self._downloader, StreamDownloader):
            self._ui.pauseButton.hide()
            self._ui.cancelButton.setText(T("stop"))
        elif isinstance(self._downloader, VideoDownloader):
            self._ui.pauseButton.show()
            self._ui.cancelButton.setText(T("cancel"))
        else:
            self._ui.pauseButton.hide()
            self._ui.cancelButton.setText(T("cancel"))
        self._ui.cancelButton.show()
        self._downloader.status.updated.connect(self._updateStatus)
        self._downloader.finished.connect(self._downloadFinishHandler)
        self._updateStatus()
        if self._downloader.isFinished():
            self._downloadFinishHandler()

    def disconnectDownloader(self) -> None:
        if self._downloader != None:
            self._ui.downloaderView.disconnectDownloader()
            self._downloader.status.updated.disconnect(self._updateStatus)
            self._downloader.finished.disconnect(self._downloadFinishHandler)
            self._retryButtonManager.deleteLater()
            self._retryButtonManager = None
            self._ui.downloadViewControlBar.retryButton.setHidden()
            self._ui.downloadViewControlBar.openFolderButton.setHidden()
            self._ui.downloadViewControlBar.openFileButton.setHidden()
            self._ui.downloadViewControlBar.openLogsButton.setHidden()
            self._ui.downloadViewControlBar.closeButton.setHidden()
            self._ui.pauseButton.hide()
            self._ui.cancelButton.hide()
            self._downloader = None
            self._widgetRemoveController.setRemoveEnabled(True)

    def _updateStatus(self) -> None:
        if self._downloader.status.pauseState.isFalse():
            self._ui.pauseButton.setText(T("pause"))
        if self._downloader.status.terminateState.isInProgress():
            self._ui.pauseButton.setEnabled(False)
            self._ui.cancelButton.setEnabled(False)
            self._ui.cancelButton.setText(T("stopping" if isinstance(self._downloader, StreamDownloader) else "canceling", ellipsis=True))
        elif not self._downloader.status.pauseState.isFalse():
            if self._downloader.status.pauseState.isInProgress():
                self._ui.pauseButton.setEnabled(False)
                self._ui.pauseButton.setText(T("pausing", ellipsis=True))
            else:
                self._ui.pauseButton.setEnabled(True)
                self._ui.pauseButton.setText(T("resume"))

    def _downloadFinishHandler(self) -> None:
        if self._downloader.status.terminateState.isTrue():
            if not (isinstance(self._downloader, StreamDownloader) and isinstance(self._downloader.status.getError(), Exceptions.AbortRequested)):
                self._ui.downloadViewControlBar.retryButton.setVisible()
        if self._downloader.status.isFileRemoved():
            self._ui.downloadViewControlBar.openFileButton.setFileNotFound()
        else:
            self._ui.downloadViewControlBar.openFileButton.setVisible()
        self._ui.downloadViewControlBar.openLogsButton.setVisible()
        self._ui.downloaderButtonArea.hide()
        self.resizedSignal.emit()
        self._widgetRemoveController.setRemoveEnabled(True)

    def tryRemoveDownloader(self) -> None:
        if not self._downloader.status.isDone():
            if self._downloader.status.terminateState.isFalse():
                if Utils.ask(*(Messages.ASK.STOP_DOWNLOAD if isinstance(self._downloader, StreamDownloader) else Messages.ASK.CANCEL_DOWNLOAD), parent=self):
                    self._downloader.cancel()
                else:
                    return
        self._widgetRemoveController.registerRemove()
        self.setEnabled(False)

    def removeDownloader(self) -> None:
        App.DownloadManager.remove(self.downloaderId)

    def pauseResume(self) -> None:
        if self._downloader.status.pauseState.isFalse():
            self._downloader.pause()
        else:
            self._downloader.resume()

    def cancel(self) -> None:
        if Utils.ask(*(Messages.ASK.STOP_DOWNLOAD if isinstance(self._downloader, StreamDownloader) else Messages.ASK.CANCEL_DOWNLOAD), parent=self):
            self._downloader.cancel()
            if self._downloader.status.terminateState.isFalse():
                Utils.info(*Messages.INFO.ACTION_PERFORM_ERROR, parent=self)

    def openFolder(self) -> None:
        if not Utils.openFolder(self._downloader.downloadInfo.directory):
            Utils.info(*Messages.INFO.FOLDER_NOT_FOUND, parent=self)

    def openFile(self) -> None:
        if not Utils.openFile(self._downloader.downloadInfo.getAbsoluteFileName()):
            Utils.info(*Messages.INFO.FILE_NOT_FOUND, parent=self)

    def openLogs(self) -> None:
        if not Utils.openFile(self._downloader.logger.getPath()):
            Utils.info(*Messages.INFO.FILE_NOT_FOUND, parent=self)