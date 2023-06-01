from PyQt6 import QtWidgets


class _QLineEdit(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs):
        super(_QLineEdit, self).__init__(*args, **kwargs)
        self._autoSelect = False
        self._cursorClickedPosition = None
        self.selectionChanged.connect(self._onSelectionChange)
        self.setClearButtonEnabled(super().isClearButtonEnabled())

    def setText(self, text):
        super().setText(text)
        self.setCursorPosition(0)

    def setClearButtonEnabled(self, enable):
        self._clearButtonEnabled = enable
        if not self.isClearButtonEnabled():
            super().setClearButtonEnabled(False)

    def isClearButtonEnabled(self):
        return self._clearButtonEnabled

    def _onSelectionChange(self):
        if self.hasSelectedText():
            self._autoSelect = False

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self._cursorClickedPosition = self.cursorPosition()

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if self._autoSelect and self._cursorClickedPosition == self.cursorPosition():
            self.selectAll()
        self._autoSelect = False
        self._cursorClickedPosition = None

    def focusInEvent(self, event):
        super().focusInEvent(event)
        if self.isClearButtonEnabled():
            super().setClearButtonEnabled(True)
        self._autoSelect = True

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        super().setClearButtonEnabled(False)
        self._autoSelect = False
QtWidgets.QLineEdit = _QLineEdit #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)