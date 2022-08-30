from PyQt5 import QtWidgets


class _QDialog(QtWidgets.QDialog):
    def exec(self):
        self.returnValue = False
        super().exec()
        return self.returnValue

    def accept(self, returnValue=True):
        self.returnValue = returnValue
        super().accept()
QtWidgets.QDialog = _QDialog #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)