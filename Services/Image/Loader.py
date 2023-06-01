from .Downloader import ImageDownloader
from .Config import Config

from Services.Threading.MutexLocker import MutexLocker
from Services.Threading.ThreadPool import ThreadPool

from PyQt6 import QtCore, QtGui


class _ImageLoader(QtCore.QObject):
    def __init__(self, parent=None):
        super(_ImageLoader, self).__init__(parent=parent)
        self.cache = {}
        self.cachingEnabled = False
        self.threadPool = ThreadPool(Config.MAX_THREAD_COUNT, parent=self)
        self._actionLock = MutexLocker()
        self.throttle(False)

    def throttle(self, throttle):
        self.threadPool.setMaxThreadCount(Config.THROTTLED_THREAD_COUNT if throttle else Config.MAX_THREAD_COUNT)

    def setCachingEnabled(self, enabled):
        self.cachingEnabled = enabled
        self._keepCacheSize()

    def isCachingEnabled(self):
        return self.cachingEnabled

    def request(self, url, callback, refresh=False):
        with self._actionLock:
            if self.cache.get(url) == None:
                self._load(url)
            elif type(self.cache[url]) == QtGui.QPixmap:
                if refresh:
                    self._load(url)
                else:
                    callback(self.cache[url])
                    return
            self.cache[url].reserve(callback)

    def cancelRequest(self, url, callback):
        with self._actionLock:
            if url in self.cache:
                if type(self.cache[url]) == ImageDownloader:
                    self.cache[url].unreserve(callback)
                    if self.cache[url].getReservationCount() == 0:
                        if self.threadPool.tryTake(self.cache[url]):
                            del self.cache[url]

    def _load(self, url):
        task = ImageDownloader(url)
        task.signals.finished.connect(self._loaded)
        self.cache[url] = task
        self.threadPool.start(task, priority=task.priority)

    def _loaded(self, task):
        with self._actionLock:
            self.cache[task.url] = task.result.data
            self._keepCacheSize()
        task.processReservedEvents()

    def _keepCacheSize(self):
        overflowedCacheSize = len(self.cache)
        if self.isCachingEnabled():
            overflowedCacheSize -= Config.CACHE_SIZE
        if overflowedCacheSize > 0:
            invalidCacheList = []
            for cache in self._findInvalidCache():
                invalidCacheList.append(cache)
                if len(invalidCacheList) == overflowedCacheSize:
                    break
            for key in invalidCacheList:
                del self.cache[key]

    def _findInvalidCache(self):
        for key, value in self.cache.items():
            if type(value) == QtGui.QPixmap:
                yield key

ImageLoader = _ImageLoader()