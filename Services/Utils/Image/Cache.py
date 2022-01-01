from .OnlineLoader import OnlineLoader
from Services.Utils.MutexLocker import MutexLocker

from PyQt5 import QtGui


class _ImageCache:
    def __init__(self):
        self.cache = {}
        self._actionLock = MutexLocker()

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

    def _load(self, url):
        self.cache[url] = OnlineLoader(url, self._loaded)

    def _loaded(self, url):
        with self._actionLock:
            loader = self.cache[url]
            loader.wait()
            self.cache[url] = loader._result
        loader.processReservedEvents()

ImageCache = _ImageCache()