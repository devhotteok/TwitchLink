from Core.Ui import *
from Download.Downloader.Core.StreamDownloader import StreamDownloader
from Download.Downloader.Core.VideoDownloader import VideoDownloader
from Download.Downloader.Core.ClipDownloader import ClipDownloader


class UpdateTrackInfoDisplay(QtWidgets.QWidget):
    def __init__(self, target: QtWidgets.QLabel, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._target = target
        self._active = False
        self._downloader: StreamDownloader | VideoDownloader | ClipDownloader | None = None
        self._updateTrackInfoTimer = QtCore.QTimer(parent=self)
        self._updateTrackInfoTimer.setInterval(200)
        self._updateTrackInfoTimer.timeout.connect(self._showUpdateTrackInfo)
        self._hide()

    def connectDownloader(self, downloader: StreamDownloader | VideoDownloader | ClipDownloader) -> None:
        self.disconnectDownloader()
        self._downloader = downloader
        self._downloader.status.updated.connect(self._updateStatus)
        self._updateStatus()

    def disconnectDownloader(self) -> None:
        if self._downloader != None:
            self._downloader.status.updated.disconnect(self._updateStatus)
            self._downloader = None
            self._hide()

    def _updateStatus(self) -> None:
        if isinstance(self._downloader, VideoDownloader) and self._downloader.downloadInfo.isUpdateTrackEnabled():
            if self._downloader.status.isDownloading() and self._downloader.status.pauseState.isFalse() and self._downloader.status.terminateState.isFalse():
                self._show()
            else:
                self._hide()
        else:
            self._hide()

    def _show(self) -> None:
        if not self._active:
            self._showUpdateTrackInfo()
            self._target.show()
            self._updateTrackInfoTimer.start()
            self._active = True

    def _hide(self) -> None:
        self._target.hide()
        if self._active:
            self._updateTrackInfoTimer.stop()
            self._active = False

    def _showUpdateTrackInfo(self) -> None:
        if self._downloader.status.getWaitingCount() == -1:
            extraStatus = f"{T('tracking-complete')}"
        elif self._downloader.status.getNextUpdateDateTime() == None:
            extraStatus = f"{T('tracking-updates', ellipsis=True)}"
        elif self._downloader.status.getWaitingCount() == 0:
            extraStatus = f"{T('next-update')}: {QtCore.QDateTime.currentDateTimeUtc().secsTo(self._downloader.status.getNextUpdateDateTime())}"
        else:
            extraStatus = f"{T('next-update')}: {QtCore.QDateTime.currentDateTimeUtc().secsTo(self._downloader.status.getNextUpdateDateTime())} / {T('no-changes-found')}: {self._downloader.status.getWaitingCount()}/{self._downloader.status.getMaxWaitingCount()}"
        self._target.setText(f"({extraStatus})")