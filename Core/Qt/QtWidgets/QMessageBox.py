from Services.Image.Presets import Icons

from PyQt6 import QtGui, QtWidgets


class _QMessageBox(QtWidgets.QMessageBox):
    def __init__(self, title, content, parent=None):
        super(_QMessageBox, self).__init__(parent=parent)
        self.setWindowIcon(QtGui.QIcon(Icons.APP_LOGO_ICON))
        self.setWindowTitle(title)
        self.setIcon(QtWidgets.QMessageBox.Icon.Information)
        self.setText(content)
QtWidgets.QMessageBox = _QMessageBox #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)