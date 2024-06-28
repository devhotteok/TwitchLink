from Services.Image.Presets import Icons

from PyQt6 import QtGui, QtWidgets


class _QMessageBox(QtWidgets.QMessageBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowIcon(Icons.APP_LOGO.icon)
        self.setIcon(QtWidgets.QMessageBox.Icon.Information)
QtWidgets.QMessageBox = _QMessageBox #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)