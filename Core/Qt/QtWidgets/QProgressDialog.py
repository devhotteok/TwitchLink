from Services.Image.Presets import Icons

from PyQt6 import QtCore, QtGui, QtWidgets


class _QProgressDialog(QtWidgets.QProgressDialog):
    def __init__(self, parent=None):
        super(_QProgressDialog, self).__init__(parent=parent)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setWindowIcon(QtGui.QIcon(Icons.APP_LOGO_ICON))
        self.progressBar = QtWidgets.QProgressBar(parent=self)
        self.setMaximum = self.progressBar.setMaximum
        self.setMinimum = self.progressBar.setMinimum
        self.setRange = self.progressBar.setRange
        self.setBar(self.progressBar)

    def reject(self):
        self.canceled.emit()
QtWidgets.QProgressDialog = _QProgressDialog #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)