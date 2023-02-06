from PyQt5 import QtCore


class WidgetRemoveController(QtCore.QObject):
    performRemove = QtCore.pyqtSignal()

    def __init__(self, parent):
        super(WidgetRemoveController, self).__init__(parent=parent)
        self._removeEnabled = True
        self._removeRegistered = False

    def setRemoveEnabled(self, enabled):
        self._removeEnabled = enabled
        if self.isRemoveEnabled() and self.isRemoveRegistered():
            self.performRemove.emit()

    def isRemoveEnabled(self):
        return self._removeEnabled

    def registerRemove(self):
        self._removeRegistered = True
        if self.isRemoveEnabled():
            self.performRemove.emit()
        else:
            self.parent().setEnabled(False)

    def isRemoveRegistered(self):
        return self._removeRegistered