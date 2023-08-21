from Core import App

from PyQt6 import QtCore, QtGui, QtWidgets


class PartnerContentWidget(QtWidgets.QWidget):
    def __init__(self, contentId: str, contentSize: QtCore.QSize, responsive: bool = False, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.contentId = contentId
        self.contentSize = contentSize
        self.responsive = responsive
        self.setLayout(QtWidgets.QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.setMinimumSize(self.contentSize)
        App.PartnerContentManager.createContent(self)

    def sizeHint(self) -> QtCore.QSize:
        return self.minimumSize()

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        App.PartnerContentManager.showContent(self)
        super().showEvent(event)

    def __del__(self):
        App.PartnerContentManager.removeContent(self)