from PyQt5 import QtWidgets


class _QProgressBar(QtWidgets.QProgressBar):
    def __init__(self, parent=None):
        super(_QProgressBar, self).__init__(parent=parent)
        self.customState = False
        self.checkRange()

    def setMaximum(self, maximum):
        super().setMaximum(maximum)
        self.checkRange()

    def setMinimum(self, minimum):
        super().setMinimum(minimum)
        self.checkRange()

    def setRange(self, minimum, maximum):
        super().setRange(minimum, maximum)
        self.checkRange()

    def checkRange(self):
        self.setTextVisible((self.minimum() != 0 or self.maximum() != 0) and not self.customState)

    def showWarning(self):
        self.showState(True, "#ffd700")

    def showError(self):
        self.showState(True, "#ff0000")

    def clearState(self):
        self.showState(False)

    def showState(self, enabled, color="#ffffff"):
        self.customState = enabled
        self.setStyleSheet(f"QProgressBar::chunk {{margin:1px;background-color: {color};}}" if self.customState else "")
        self.checkRange()
QtWidgets.QProgressBar = _QProgressBar #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)