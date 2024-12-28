from PyQt6 import QtCore, QtWidgets


class _QTabBar(QtWidgets.QTabBar):
    def tabSizeHint(self, index: int) -> QtCore.QSize:
        if self.shape() in (_QTabBar.Shape.RoundedNorth, _QTabBar.Shape.RoundedSouth, _QTabBar.Shape.TriangularNorth, _QTabBar.Shape.TriangularSouth):
            width = max(min(int(max(self.parent().width(), 200) / (self.count() or 1)), 200), 100)
            height = super().tabSizeHint(index).height() + 10
            return QtCore.QSize(width, height)
        else:
            return super().tabSizeHint(index)
QtWidgets.QTabBar = _QTabBar #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)