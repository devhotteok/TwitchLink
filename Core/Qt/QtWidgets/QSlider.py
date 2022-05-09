from PyQt5 import QtWidgets


class _QSlider(QtWidgets.QSlider):
    def setValueSilent(self, value):
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)
QtWidgets.QSlider = _QSlider