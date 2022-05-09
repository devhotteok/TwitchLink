from PyQt5 import QtWidgets


class _QLineEdit(QtWidgets.QLineEdit):
    def setText(self, text):
        super().setText(text)
        self.setCursorPosition(0)
QtWidgets.QLineEdit = _QLineEdit