from PyQt6 import QtCore, QtWidgets


class TimedCancelDialog(QtWidgets.QProgressDialog):
    def __init__(self, title, content, time=10, parent=None):
        super(TimedCancelDialog, self).__init__(parent=parent)
        self.setWindowTitle(title)
        self.content = content
        self.progressBar.setTextVisible(False)
        self.canceled.connect(self.cancelRequested)
        self.totalTime = time
        self.timeRemaining = self.totalTime
        self.showTimeRemaining()
        self.timer = QtCore.QTimer(parent=self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.timeout)
        self.timer.start()

    def timeout(self):
        self.timeRemaining -= 1
        self.showTimeRemaining()
        if self.timeRemaining == 0:
            self.timer.stop()

    def showTimeRemaining(self):
        self.setLabelText(self.content.format(seconds=self.timeRemaining))
        self.setValue(int(100 - (self.timeRemaining / self.totalTime) * 100))

    def cancelRequested(self):
        self.timer.stop()