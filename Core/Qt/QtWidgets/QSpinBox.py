from PyQt5 import QtWidgets


class _QSpinBox(QtWidgets.QSpinBox):
    def setValueSilent(self, value):
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)
QtWidgets.QSpinBox = _QSpinBox