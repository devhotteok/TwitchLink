from Core import App
from Services.Image.UrlFormatter import ImageUrlFormatter

from PyQt6 import QtCore, QtGui, QtWidgets


class _QLabel(QtWidgets.QLabel):
    imageChanged = QtCore.pyqtSignal(QtGui.QPixmap)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._autoToolTipEnabled = True
        self._text = super().text()
        self._pixmap = super().pixmap()
        self._imageUrl = ""
        self._imageLoading = False
        self.setKeepAspectRatio(False)
        self._imageSynced = False

    def loadImage(self, filePath: str, url: str = "", urlFormatSize: tuple[int | None, int | None] | None = None, refresh: bool = False, clearImage: bool = True) -> None:
        self.cancelImageRequest()
        if url == "" or self._imageUrl == "" or clearImage:
            self.setPixmap(QtGui.QPixmap(filePath))
        self._imageUrl = ImageUrlFormatter.formatUrl(url) if urlFormatSize == None else ImageUrlFormatter.formatUrl(url, *urlFormatSize)
        if self._imageUrl != "":
            self._imageLoading = True
            App.ImageLoader.request(QtCore.QUrl(self._imageUrl), self._imageLoaded, refresh=refresh)

    def getImageUrl(self) -> str:
        return self._imageUrl

    def _imageLoaded(self, pixmap: QtGui.QPixmap) -> None:
        if not pixmap.isNull():
            self.setPixmap(pixmap)
        self._imageLoading = False

    def pixmap(self) -> QtGui.QPixmap:
        return self._pixmap

    def setPixmap(self, pixmap: QtGui.QPixmap) -> None:
        self._pixmap = pixmap
        if self._keepAspectRatio:
            super().setPixmap(self.getScaledPixmap())
        else:
            super().setPixmap(self._pixmap)
        self.imageChanged.emit(self._pixmap)

    def getScaledPixmap(self) -> QtGui.QPixmap:
        margins = self.contentsMargins()
        size = self.size() - QtCore.QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return self.pixmap().scaled(size, QtCore.Qt.AspectRatioMode.KeepAspectRatio, QtCore.Qt.TransformationMode.SmoothTransformation)

    def syncImage(self, target: QtWidgets.QLabel) -> None:
        self._imageSynced = True
        target.imageChanged.connect(self.setPixmap)
        pixmap = target.pixmap()
        if not pixmap.isNull():
            self.setPixmap(pixmap)

    def isImageSynced(self) -> bool:
        return self._imageSynced

    def cancelImageRequest(self) -> None:
        if self._imageLoading:
            App.ImageLoader.cancelRequest(QtCore.QUrl(self._imageUrl), self._imageLoaded)
            self._imageLoading = False

    def setImageSizePolicy(self, minimumSize: QtCore.QSize, maximumSize: QtCore.QSize, keepAspectRatio: bool = True) -> None:
        self.setMinimumSize(minimumSize)
        self.setMaximumSize(maximumSize)
        self.setKeepAspectRatio(keepAspectRatio)

    def setKeepAspectRatio(self, keepAspectRatio: bool) -> None:
        self._keepAspectRatio = keepAspectRatio
        self.setScaledContents(not self._keepAspectRatio)

    def text(self) -> str:
        return self._text

    def setText(self, text: str) -> None:
        if isinstance(text, QtCore.QDateTime):
            self._text = text.toTimeZone(App.Preferences.localization.getTimezone()).toString("yyyy-MM-dd HH:mm:ss")
            self._autoToolTipEnabled = False
            self.setToolTip(f"{self._text} ({App.Preferences.localization.getTimezone().name()})")
        else:
            self._text = str(text)
            self._autoToolTipEnabled = True
        super().setText(self._text)

    def getElidedText(self) -> str:
        metrics = QtGui.QFontMetrics(self.font())
        text = "\n".join([metrics.elidedText(text, QtCore.Qt.TextElideMode.ElideRight, self.width()) for text in self.text().splitlines()])
        return text

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        if not self.pixmap().isNull():
            if self._keepAspectRatio:
                super().setPixmap(self.getScaledPixmap())
        super().resizeEvent(event)

    def paintEvent(self, event: QtGui.QPaintEvent | None) -> None:
        if self.pixmap().isNull() and not self.hasSelectedText():
            painter = QtGui.QPainter(self)
            text = self.getElidedText()
            painter.drawText(self.rect(), self.alignment(), text)
            if self._autoToolTipEnabled:
                self.setToolTip("" if text == self.text() else self.text())
        else:
            super().paintEvent(event)

    def __del__(self):
        self.cancelImageRequest()
QtWidgets.QLabel = _QLabel #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)