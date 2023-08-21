from PyQt6 import QtGui, QtWidgets


class _QLineEdit(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._autoSelect = False
        self._cursorClickedPosition = None
        self._clearButtonEnabled = super().isClearButtonEnabled()
        self.selectionChanged.connect(self._onSelectionChange)

    def setText(self, text: str) -> None:
        super().setText(text)
        self.setCursorPosition(0)

    def setClearButtonEnabled(self, enable: bool) -> None:
        self._clearButtonEnabled = enable
        if not self.isClearButtonEnabled():
            super().setClearButtonEnabled(False)

    def isClearButtonEnabled(self) -> bool:
        return self._clearButtonEnabled

    def _onSelectionChange(self) -> None:
        if self.hasSelectedText():
            self._autoSelect = False

    def mousePressEvent(self, event: QtGui.QMouseEvent | None) -> None:
        super().mousePressEvent(event)
        self._cursorClickedPosition = self.cursorPosition()

    def mouseReleaseEvent(self, event: QtGui.QMouseEvent | None) -> None:
        super().mouseReleaseEvent(event)
        if self._autoSelect and self._cursorClickedPosition == self.cursorPosition():
            self.selectAll()
        self._autoSelect = False
        self._cursorClickedPosition = None

    def focusInEvent(self, event: QtGui.QFocusEvent | None) -> None:
        super().focusInEvent(event)
        if self.isClearButtonEnabled():
            super().setClearButtonEnabled(True)
        self._autoSelect = True

    def focusOutEvent(self, event: QtGui.QFocusEvent | None) -> None:
        super().focusOutEvent(event)
        super().setClearButtonEnabled(False)
        self._autoSelect = False
QtWidgets.QLineEdit = _QLineEdit #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)