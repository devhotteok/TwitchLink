from Services.Image.Presets import Icons

from PyQt6 import QtCore, QtWidgets


class _QProgressDialog(QtWidgets.QProgressDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowFlag(QtCore.Qt.WindowType.WindowContextHelpButtonHint, False)
        self.setWindowIcon(Icons.APP_LOGO.icon)
        self.progressBar = QtWidgets.QProgressBar(parent=self)
        self.setMaximum = self.progressBar.setMaximum
        self.setMinimum = self.progressBar.setMinimum
        self.setRange = self.progressBar.setRange
        self.setBar(self.progressBar)
QtWidgets.QProgressDialog = _QProgressDialog #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)