from .AdView import AdView

from PyQt6 import QtCore


class CachedAd(QtCore.QObject):
    noReferenceFound = QtCore.pyqtSignal(object)

    def __init__(self, adId, adSize, parent=None):
        super(CachedAd, self).__init__(parent=parent)
        self.adId = adId
        self.references = []
        self.adObject = AdView()
        self.adObject.getAd(adSize.width(), adSize.height())

    def addReference(self, widgetId):
        if widgetId not in self.references:
            self.references.append(widgetId)

    def removeReference(self, widgetId):
        self.references.remove(widgetId)
        if len(self.references) == 0:
            self.noReferenceFound.emit(self.adId)


class _AdManager(QtCore.QObject):
    def __init__(self, parent=None):
        super(_AdManager, self).__init__(parent=parent)
        self.cache = {}

    def setAd(self, adWidget):
        if adWidget.adId not in self.cache:
            cachedAd = CachedAd(adId=adWidget.adId, adSize=adWidget.adSize, parent=self)
            cachedAd.noReferenceFound.connect(self._removeCache)
            self.cache[adWidget.adId] = cachedAd
        self.cache[adWidget.adId].addReference(id(adWidget))
        self.cache[adWidget.adId].adObject.moveTo(adWidget)

    def removeAd(self, adWidget):
        if adWidget.adId in self.cache:
            self.cache[adWidget.adId].removeReference(id(adWidget))

    def _removeCache(self, adId):
        self.cache.pop(adId).setParent(None)

AdManager = _AdManager()