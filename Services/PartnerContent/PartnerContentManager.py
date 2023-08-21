from .PartnerContentView import PartnerContentView
from .PartnerContentWidget import PartnerContentWidget

from PyQt6 import QtCore


class CachedContent(QtCore.QObject):
    removeRequested = QtCore.pyqtSignal(object)

    def __init__(self, contentId: str, contentSize: QtCore.QSize, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.contentId = contentId
        self._references = []
        self.contentObject = PartnerContentView(parent=None)
        self.contentObject.getContent(contentSize.width(), contentSize.height())

    def addReference(self, widgetId: int) -> None:
        if widgetId not in self._references:
            self._references.append(widgetId)

    def removeReference(self, widgetId: int) -> None:
        self._references.remove(widgetId)
        if len(self._references) == 0:
            self.removeRequested.emit(self.contentId)

    def getReferenceCount(self) -> int:
        return len(self._references)


class PartnerContentManager(QtCore.QObject):
    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.cache = {}

    def createContent(self, partnerContentWidget: PartnerContentWidget) -> None:
        if partnerContentWidget.contentId not in self.cache:
            cachedContent = CachedContent(contentId=partnerContentWidget.contentId, contentSize=partnerContentWidget.contentSize, parent=self)
            cachedContent.removeRequested.connect(self._removeCache)
            self.cache[partnerContentWidget.contentId] = cachedContent
        self.cache[partnerContentWidget.contentId].addReference(id(partnerContentWidget))
        parent = self.cache[partnerContentWidget.contentId].contentObject.parent()
        self.cache[partnerContentWidget.contentId].contentObject.moveTo(partnerContentWidget)
        if parent != None:
            self.cache[partnerContentWidget.contentId].contentObject.moveTo(parent)

    def removeContent(self, partnerContentWidget: PartnerContentWidget) -> None:
        if partnerContentWidget.contentId in self.cache:
            self.cache[partnerContentWidget.contentId].removeReference(id(partnerContentWidget))

    def showContent(self, partnerContentWidget: PartnerContentWidget) -> None:
        if partnerContentWidget.contentId in self.cache:
            self.cache[partnerContentWidget.contentId].contentObject.moveTo(partnerContentWidget)

    def _removeCache(self, contentId: str) -> None:
        if self.cache[contentId].getReferenceCount() == 0:
            self.cache.pop(contentId).deleteLater()