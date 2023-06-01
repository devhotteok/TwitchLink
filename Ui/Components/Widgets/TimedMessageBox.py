from PyQt6 import QtCore, QtWidgets


class TimedMessageBox(QtWidgets.QMessageBox):
    def __init__(self, title, content, defaultButton=None, autoClickButton=None, buttons=None, time=10, parent=None):
        super(TimedMessageBox, self).__init__(title, content, parent=parent)
        self.totalTime = time
        self.timeRemaining = self.totalTime
        self.timer = QtCore.QTimer(parent=self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.timeout)
        self.setDefaultButton(self.addButton(defaultButton or autoClickButton or self.StandardButton.Ok))
        self.autoClickButton = self.defaultButton() if defaultButton == None or autoClickButton == None else self.addButton(autoClickButton)
        self.autoClickButtonText = self.autoClickButton.text()
        if buttons != None:
            for button in buttons:
                self.addButton(button)

    def exec(self):
        self.showTimeRemaining()
        self.timer.start()
        return super().exec()

    def timeout(self):
        self.timeRemaining -= 1
        self.showTimeRemaining()
        if self.timeRemaining == 0:
            self.timer.stop()
            self.autoClickButton.click()

    def showTimeRemaining(self):
        self.autoClickButton.setText(f"{self.autoClickButtonText} ({self.timeRemaining})")

    def cancelRequested(self):
        self.timer.stop()