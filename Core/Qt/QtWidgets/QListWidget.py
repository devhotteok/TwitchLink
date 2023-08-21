from PyQt6 import QtGui, QtWidgets


class _QListWidget(QtWidgets.QListWidget):
    def addItem(self, item: QtWidgets.QListWidgetItem | None) -> None:
        super().addItem(item)
        if isinstance(item, QtWidgets.QListWidgetItem):
            minimumWidth = item.sizeHint().width() + self.verticalScrollBar().sizeHint().width()
            if minimumWidth > self.minimumWidth():
                self.setMinimumWidth(minimumWidth)

    def takeItem(self, row: int) -> QtWidgets.QListWidgetItem | None:
        item = super().takeItem(row)
        if item != None:
            minimumWidth = item.sizeHint().width() + self.verticalScrollBar().sizeHint().width()
            if minimumWidth == self.minimumWidth():
                self._updateMinimumWidth()
        return item

    def clear(self) -> None:
        super().clear()
        self._updateMinimumWidth()

    def _updateMinimumWidth(self) -> None:
        minWidth = max((self.item(index).sizeHint().width() for index in range(self.count())), default=0)
        self.setMinimumWidth(minWidth + self.verticalScrollBar().sizeHint().width())

    def resizeEvent(self, event: QtGui.QResizeEvent | None) -> None:
        self.updateGeometries()
        super().resizeEvent(event)
QtWidgets.QListWidget = _QListWidget #Direct Class Patch - [Warning] Does not affect embedded objects (Use with caution)