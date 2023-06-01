from .AdManager import AdManager

from PyQt6 import QtWidgets


class AdWidget(QtWidgets.QWidget):
    def __init__(self, adId, adSize, responsive=False, parent=None):
        super(AdWidget, self).__init__(parent=parent)
        self.adId = adId
        self.adSize = adSize
        self.responsive = responsive
        self.setLayout(QtWidgets.QHBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(self.adSize)
        self._connected = False

    def sizeHint(self):
        return self.minimumSize()

    def showEvent(self, event):
        try:
            AdManager.setAd(self)
            self._connected = True
        except:
            self.hide()
        super().showEvent(event)

    def __del__(self):
        if self._connected:
            AdManager.removeAd(self)