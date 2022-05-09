from PyQt5 import QtWidgets


class _QListWidget(QtWidgets.QListWidget):
    def resizeEvent(self, event):
        self.updateGeometries()
        super().resizeEvent(event)
QtWidgets.QListWidget = _QListWidget