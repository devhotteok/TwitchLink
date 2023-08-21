from .PartnerContentWidget import PartnerContentWidget
from .Config import Config

from Ui.Components.Operators import WidgetListViewer

from PyQt6 import QtCore, QtWidgets


class PartnerContentInFeedWidgetListViewerItem(WidgetListViewer.WidgetListViewerItem):
    def __init__(self, widget: QtWidgets.QWidget, index: int = 0, resizeSignal: QtCore.pyqtSignal | None = None):
        super().__init__(widget, resizeSignal)
        self._index = index

    def setIndex(self, index: int) -> None:
        self._index = index

    def __lt__(self, other):
        return self._index < other._index

    def __le__(self, other):
        return self._index <= other._index

    def __gt__(self, other):
        return self._index > other._index

    def __ge__(self, other):
        return self._index >= other._index


class PartnerContentInFeedWidgetListViewer(WidgetListViewer.WidgetListViewer):
    def __init__(self, listWidget: QtWidgets.QListWidget, partnerContentSize: QtCore.QSize | None = None, responsive: bool = True, parent: QtCore.QObject | None = None):
        super().__init__(listWidget, parent=parent)
        self._partnerContentSize = partnerContentSize
        self._responsive = responsive
        self._partnerContentItems = []
        self._autoReload = True

    def setAutoReloadEnabled(self, enabled: bool) -> None:
        self._autoReload = enabled
        if self._autoReload:
            self._reload()

    def _getPartnerContentSize(self) -> QtCore.QSize:
        return self._contentItems[0].sizeHint() if self._partnerContentSize == None else self._partnerContentSize

    def addWidget(self, widget: QtWidgets.QWidget, resizeSignal: QtCore.pyqtSignal | None = None) -> None:
        super().addWidget(widget, resizeSignal)
        if self._autoReload:
            self._reload()

    def insertWidget(self, index: int, widget: QtWidgets.QWidget, resizeSignal: QtCore.pyqtSignal | None = None) -> None:
        super().insertWidget(index, widget, resizeSignal)
        if self._autoReload:
            self._reload()

    def removeWidget(self, widget: QtWidgets.QWidget) -> None:
        super().removeWidget(widget)
        if self._autoReload:
            self._reload()

    def clear(self) -> None:
        super().clear()
        self._partnerContentItems.clear()

    def _createWidgetListViewerItem(self, widget: QtWidgets.QWidget, resizeSignal: QtCore.pyqtSignal | None = None) -> PartnerContentInFeedWidgetListViewerItem:
        return PartnerContentInFeedWidgetListViewerItem(widget, resizeSignal=resizeSignal)

    def _reload(self) -> None:
        for index, value in enumerate(self._contentItems):
            value.setIndex(index * 2)
        if Config.ENABLED and Config.IN_FEED_FREQUENCY != 0:
            while len(self._contentItems) // Config.IN_FEED_FREQUENCY > len(self._partnerContentItems):
                self._createPartnerContent()
            while len(self._contentItems) // Config.IN_FEED_FREQUENCY < len(self._partnerContentItems):
                self._removePartnerContent()
        else:
            while len(self._partnerContentItems) != 0:
                self._removePartnerContent()
        self._listWidget.sortItems()

    def _createPartnerContent(self) -> None:
        index = (len(self._partnerContentItems) + 1) * Config.IN_FEED_FREQUENCY
        partnerContentWidget = PartnerContentWidget(
            contentId=f"InFeed.{self._getPartnerContentSize().width()}x{self._getPartnerContentSize().height()}-{index}",
            contentSize=self._getPartnerContentSize(),
            responsive=self._responsive,
            parent=None
        )
        item = self._createWidgetListViewerItem(partnerContentWidget)
        item.widget.setContentsMargins(0, 0, 0, 0)
        item.setIndex(index * 2 - 1)
        self._listWidget.addItem(item)
        self._listWidget.setItemWidget(item, item.widget)
        self._partnerContentItems.append(item)

    def _removePartnerContent(self) -> None:
        self._listWidget.takeItem(self._listWidget.row(self._partnerContentItems.pop()))

    def _itemClicked(self, item: PartnerContentInFeedWidgetListViewerItem) -> None:
        if item in self._contentItems:
            super()._itemClicked(item)