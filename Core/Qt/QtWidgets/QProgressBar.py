from PyQt6 import QtWidgets


class _QProgressBar(QtWidgets.QProgressBar):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._customState = False
        self._checkRange()

    def setMaximum(self, maximum: int) -> None:
        super().setMaximum(maximum)
        self._checkRange()

    def setMinimum(self, minimum: int) -> None:
        super().setMinimum(minimum)
        self._checkRange()

    def setRange(self, minimum: int, maximum: int) -> None:
        super().setRange(minimum, maximum)
        self._checkRange()

    def _checkRange(self) -> None:
        self.setTextVisible((self.minimum() != 0 or self.maximum() != 0) and not self._customState)

    def showWarning(self) -> None:
        self.showState(True, "#ffd700")

    def showError(self) -> None:
        self.showState(True, "#ff0000")

    def clearState(self) -> None:
        self.showState(False)

    def showState(self, enabled: bool, color: str = "#ffffff") -> None:
        self._customState = enabled
        self.setStyleSheet(f"QProgressBar::chunk {{margin:1px;background-color: {color};}}" if self._customState else "")
        self._checkRange()
QtWidgets.QProgressBar = _QProgressBar #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)