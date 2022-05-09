from Services.Threading.WorkerThread import WorkerThread

from PyQt5 import QtCore, QtWidgets


class ProgressDialog(QtWidgets.QProgressDialog):
    def __init__(self, cancelAllowed=True, parent=None):
        super(ProgressDialog, self).__init__(parent=parent)
        self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
        self.setAutoReset(False)
        self.cancelAllowed = cancelAllowed
        if not self.cancelAllowed:
            self.setCancelButton(None)
        self.cancelRequested = False
        self.canceled.disconnect(self.cancel)
        self.canceled.connect(self.requestCancel)

    @property
    def cancelButton(self):
        return self.findChild(QtWidgets.QPushButton)

    def requestCancel(self):
        if self.cancelAllowed and not self.cancelRequested:
            self.cancelRequested = True
            self.thread.requestInterruption()
            self.cancelButton.setEnabled(False)

    def exec(self, target):
        self.returnValue = False
        self.thread = WorkerThread(target=target, parent=self)
        self.thread.finished.connect(self.accept)
        self.thread.start()
        super().exec()
        return self.returnValue

    def accept(self, returnValue=True):
        self.returnValue = returnValue
        if self.cancelRequested:
            self.cancel()
        else:
            super().accept()

    def reject(self):
        self.requestCancel()