from PyQt6 import QtWidgets


class _QComboBox_Patcher(QtWidgets.QComboBox):
    def setCurrentIndexSilent(self, index: int) -> None:
        self.blockSignals(True)
        self.setCurrentIndex(index)
        self.blockSignals(False)
QtWidgets.QComboBox.setCurrentIndexSilent = _QComboBox_Patcher.setCurrentIndexSilent #Direct Attribute Patch - [Info] Affects all embedded objects