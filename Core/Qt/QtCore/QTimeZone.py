from PyQt6 import QtCore


class _QTimeZone_Patcher(QtCore.QTimeZone):
    def name(self):
        return self.id().data().decode()
QtCore.QTimeZone.name = _QTimeZone_Patcher.name #Direct Attribute Patch - [Info] Affects all embedded objects