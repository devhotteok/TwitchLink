from PyQt5 import QtWidgets


class _QProgressBar(QtWidgets.QProgressBar):
    def __init__(self, parent=None):
        super(_QProgressBar, self).__init__(parent=parent)
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
        self.setTextVisible(self.minimum() != 0 or self.maximum() != 0)
QtWidgets.QProgressBar = _QProgressBar