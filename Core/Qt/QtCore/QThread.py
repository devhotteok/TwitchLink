from PyQt5 import QtCore


class _QThread(QtCore.QThread):
    def __init__(self, parent=None):
        super(_QThread, self).__init__(parent=parent)
        if parent != None:
            parent.destroyed.connect(self.parentDestroyed)

    def setParent(self, parent):
        if self.parent() != None:
            self.parent().destroyed.disconnect(self.parentDestroyed)
        super().setParent(parent)
        if parent != None:
            parent.destroyed.connect(self.parentDestroyed)

    def parentDestroyed(self):
        if self.isRunning():
            self.requestInterruption()
            self.setParent(None)
QtCore.QThread = _QThread #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)