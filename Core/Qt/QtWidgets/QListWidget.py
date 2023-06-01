from PyQt6 import QtWidgets


class _QListWidget(QtWidgets.QListWidget):
    def resizeEvent(self, event):
        self.updateGeometries()
        super().resizeEvent(event)
QtWidgets.QListWidget = _QListWidget #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)