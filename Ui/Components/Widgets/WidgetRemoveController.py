from PyQt6 import QtCore


class WidgetRemoveController(QtCore.QObject):
    performRemove = QtCore.pyqtSignal()

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._removeEnabled = True
        self._removeRegistered = False

    def setRemoveEnabled(self, enabled: bool) -> None:
        if self._removeEnabled != enabled:
            self._removeEnabled = enabled
            if self.isRemoveEnabled() and self.isRemoveRegistered():
                self.performRemove.emit()

    def isRemoveEnabled(self) -> bool:
        return self._removeEnabled

    def registerRemove(self) -> None:
        if not self._removeRegistered:
            self._removeRegistered = True
            if self.isRemoveEnabled():
                self.performRemove.emit()

    def isRemoveRegistered(self) -> bool:
        return self._removeRegistered