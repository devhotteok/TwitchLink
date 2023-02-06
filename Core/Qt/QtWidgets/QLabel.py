from Services.Image.UrlFormatter import ImageUrlFormatter
from Services.Image.Loader import ImageLoader

from PyQt5 import QtCore, QtGui, QtWidgets


class _QLabel(QtWidgets.QLabel):
    imageChanged = QtCore.pyqtSignal(QtGui.QPixmap)

    def __init__(self, *args, **kwargs):
        super(_QLabel, self).__init__(*args, **kwargs)
        self._useAutoToolTip = True
        self._imageUrl = ""
        self._imageLoading = False
        self._keepImageRatio = False
        self._imageSynced = False

    def loadImage(self, filePath, url="", urlFormatSize=None, refresh=False, clearImage=True):
        self.cancelImageRequest()
        if url == "" or self._imageUrl == "" or clearImage:
            pixmap = QtGui.QPixmap(filePath)
            self.setPixmap(pixmap)
        self._imageUrl = ImageUrlFormatter.formatUrl(url) if urlFormatSize == None else ImageUrlFormatter.formatUrl(url, *urlFormatSize)
        if self._imageUrl != "":
            self._imageLoading = True
            ImageLoader.request(self._imageUrl, self._imageLoaded, refresh=refresh)

    def getImageUrl(self):
        return self._imageUrl

    def _imageLoaded(self, pixmap):
        if pixmap != None:
            self.setPixmap(pixmap)
        self._imageLoading = False

    def setPixmap(self, pixmap):
        super().setPixmap(pixmap)
        self.imageChanged.emit(pixmap)

    def syncImage(self, target):
        self._imageSynced = True
        target.imageChanged.connect(self.setPixmap)
        pixmap = target.pixmap()
        if pixmap != None:
            self.setPixmap(pixmap)

    def isImageSynced(self):
        return self._imageSynced

    def cancelImageRequest(self):
        if self._imageLoading:
            try:
                ImageLoader.cancelRequest(self._imageUrl, self._imageLoaded)
            except:
                pass
            self._imageLoading = False

    def setImageSizePolicy(self, minimumSize, maximumSize, keepImageRatio=True):
        self.setMinimumSize(*minimumSize)
        self.setMaximumSize(*maximumSize)
        self.keepImageRatio(keepImageRatio)

    def keepImageRatio(self, keepImageRatio):
        self._keepImageRatio = keepImageRatio

    def setText(self, text):
        if isinstance(text, QtCore.QDateTime):
            timeString = text.toString("yyyy-MM-dd HH:mm:ss")
            super().setText(timeString)
            self._useAutoToolTip = False
            self.setToolTip(f"{timeString} ({text.timeZone().name()})")
        else:
            super().setText(str(text))
            self._useAutoToolTip = True

    def paintEvent(self, event):
        if self.pixmap() == None:
            if self.hasSelectedText():
                super().paintEvent(event)
            else:
                painter = QtGui.QPainter(self)
                metrics = QtGui.QFontMetrics(self.font())
                text = "\n".join([metrics.elidedText(text, QtCore.Qt.ElideRight, self.width()) for text in self.text().split("\n")])
                painter.drawText(self.rect(), self.alignment(), text)
                if self._useAutoToolTip:
                    self.setToolTip("" if text == self.text() else self.text())
        else:
            if self._keepImageRatio:
                margins = self.getContentsMargins()
                size = self.size() - QtCore.QSize(margins[0] + margins[2], margins[1] + margins[3])
                painter = QtGui.QPainter(self)
                point = QtCore.QPoint(0, 0)
                scaledPix = self.pixmap().scaled(size, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
                point.setX(int((size.width() - scaledPix.width()) / 2) + margins[0])
                point.setY(int((size.height() - scaledPix.height()) / 2) + margins[1])
                painter.drawPixmap(point, scaledPix)
            else:
                super().paintEvent(event)

    def __del__(self):
        self.cancelImageRequest()
QtWidgets.QLabel = _QLabel #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)