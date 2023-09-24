from PyQt6 import QtCore, QtWidgets


class WidgetListViewerItem(QtWidgets.QListWidgetItem):
    def __init__(self, widget: QtWidgets.QWidget, resizeSignal: QtCore.pyqtSignal | None = None):
        super().__init__(parent=None)
        self.widget = widget
        self.widget.setContentsMargins(10, 10, 10, 10)
        self._resize()
        if resizeSignal != None:
            resizeSignal.connect(self._resize, QtCore.Qt.ConnectionType.QueuedConnection)

    def _resize(self) -> None:
        self.setSizeHint(self.widget.sizeHint())


class WidgetListViewer(QtCore.QObject):
    widgetClicked = QtCore.pyqtSignal(QtWidgets.QWidget)

    def __init__(self, listWidget: QtWidgets.QListWidget, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._listWidget = listWidget
        self._listWidget.itemSelectionChanged.connect(self._listWidget.clearSelection)
        self._listWidget.itemClicked.connect(self._itemClicked)
        self._listWidget.verticalScrollBar().setSingleStep(30)
        self._contentItems = []

    def count(self) -> int:
        return len(self._contentItems)

    def addWidget(self, widget: QtWidgets.QWidget, resizeSignal: QtCore.pyqtSignal | None = None) -> None:
        item = self._createWidgetListViewerItem(widget, resizeSignal)
        self._listWidget.addItem(item)
        self._listWidget.setItemWidget(item, item.widget)
        self._contentItems.append(item)

    def insertWidget(self, index: int, widget: QtWidgets.QWidget, resizeSignal: QtCore.pyqtSignal | None = None) -> None:
        item = self._createWidgetListViewerItem(widget, resizeSignal)
        self._listWidget.insertItem(index, item)
        self._listWidget.setItemWidget(item, item.widget)
        self._contentItems.insert(index, item)

    def removeWidget(self, widget: QtWidgets.QWidget) -> None:
        item = next(contentItem for contentItem in self._contentItems if contentItem.widget == widget)
        self._listWidget.takeItem(self._listWidget.row(item))
        self._contentItems.remove(item)

    def clear(self) -> None:
        self._listWidget.clear()
        self._contentItems.clear()

    def setHidden(self, widget: QtWidgets.QWidget, hidden: bool) -> None:
        next(contentItem for contentItem in self._contentItems if contentItem.widget == widget).setHidden(hidden)

    def isHidden(self, widget: QtWidgets.QWidget) -> bool:
        return next(contentItem for contentItem in self._contentItems if contentItem.widget == widget).isHidden()

    def _createWidgetListViewerItem(self, widget: QtWidgets.QWidget, resizeSignal: QtCore.pyqtSignal | None = None) -> WidgetListViewerItem:
        return WidgetListViewerItem(widget, resizeSignal=resizeSignal)

    def _itemClicked(self, item: WidgetListViewerItem) -> None:
        self.widgetClicked.emit(item.widget)