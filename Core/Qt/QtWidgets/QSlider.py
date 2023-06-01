from PyQt6 import QtWidgets


class _QSlider_Patcher(QtWidgets.QSlider):
    def setValueSilent(self, value):
        self.blockSignals(True)
        self.setValue(value)
        self.blockSignals(False)
QtWidgets.QSlider.setValueSilent = _QSlider_Patcher.setValueSilent #Direct Attribute Patch - [Info] Affects all embedded objects