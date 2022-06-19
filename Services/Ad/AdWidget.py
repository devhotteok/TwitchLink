from .AdManager import AdManager

from PyQt5 import QtWidgets


class AdWidget(QtWidgets.QWidget):
    def __init__(self, adId, adSize, responsive=False, parent=None):
        super(AdWidget, self).__init__(parent=parent)
        self.adId = adId
        self.adSize = adSize
        self.setLayout(QtWidgets.QHBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        if responsive:
            self.setMinimumSize(self.adSize)
        else:
            self.setFixedSize(self.adSize)

    def sizeHint(self):
        return self.minimumSize()

    def showEvent(self, event):
        AdManager.setAd(self)
        super().showEvent(event)

    def __del__(self):
        AdManager.removeAd(self)