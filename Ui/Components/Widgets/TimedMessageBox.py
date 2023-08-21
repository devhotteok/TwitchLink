from PyQt6 import QtCore, QtWidgets


class TimedMessageBox(QtWidgets.QMessageBox):
    def __init__(self, title: str, content: str, defaultButton: QtWidgets.QMessageBox.StandardButton | None = None, autoClickButton: QtWidgets.QMessageBox.StandardButton | None = None, time: int = 10, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.setWindowTitle(title)
        self.setText(content)
        self.totalTime = time
        self.timeRemaining = self.totalTime
        self.timer = QtCore.QTimer(parent=self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._onTimeout)
        self.setDefaultButton(self.addButton(defaultButton or autoClickButton or self.StandardButton.Ok))
        self.autoClickButton = self.defaultButton() if defaultButton == None or autoClickButton == None else self.addButton(autoClickButton)
        self._autoClickButtonText = self.autoClickButton.text()

    def exec(self) -> int:
        self._showTimeRemaining()
        self.timer.start()
        return super().exec()

    def _onTimeout(self) -> None:
        self.timeRemaining -= 1
        self._showTimeRemaining()
        if self.timeRemaining == 0:
            self.timer.stop()
            self.autoClickButton.click()

    def _showTimeRemaining(self) -> None:
        self.autoClickButton.setText(f"{self._autoClickButtonText} ({self.timeRemaining})")