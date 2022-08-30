from Services.Image.Presets import Images

from PyQt5 import QtCore, QtGui, QtWidgets


class _QProgressDialog(QtWidgets.QProgressDialog):
    def __init__(self, parent=None):
        super(_QProgressDialog, self).__init__(parent=parent)
        self.setWindowFlag(QtCore.Qt.WindowContextHelpButtonHint, False)
        self.setWindowIcon(QtGui.QIcon(Images.APP_LOGO_IMAGE))
        self.progressBar = QtWidgets.QProgressBar(parent=self)
        self.setMaximum = self.progressBar.setMaximum
        self.setMinimum = self.progressBar.setMinimum
        self.setRange = self.progressBar.setRange
        self.setBar(self.progressBar)

    def reject(self):
        self.canceled.emit()
QtWidgets.QProgressDialog = _QProgressDialog #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)