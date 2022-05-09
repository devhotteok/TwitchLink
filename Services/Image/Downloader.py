from Core.GlobalExceptions import Exceptions
from Services.NetworkRequests import Network
from Services.Threading.MutexLocker import MutexLocker
from Services.Task.PrioritizedTask import PrioritizedTask, TaskSignals

from PyQt5 import QtCore, QtGui


class ImageDownloaderSignals(TaskSignals):
    imageLoaded = QtCore.pyqtSignal(object)


class ImageDownloader(PrioritizedTask):
    def __init__(self, url):
        super(ImageDownloader, self).__init__(signals=ImageDownloaderSignals)
        self.url = url
        self.image = None
        self.connectionCount = 0
        self._actionLock = MutexLocker()

    def task(self):
        try:
            data = Network.session.get(self.url)
            if data.status_code == 200:
                image = QtGui.QImage()
                image.loadFromData(data.content)
                self.image = QtGui.QPixmap(image)
                return self.image
            else:
                raise
        except:
            raise Exceptions.NetworkError

    def reserve(self, callback):
        with self._actionLock:
            self.connectionCount += 1
        self.signals.imageLoaded.connect(callback)

    def unreserve(self, callback):
        try:
            self.signals.imageLoaded.disconnect(callback)
            with self._actionLock:
                self.connectionCount -= 1
        except:
            pass

    def getReservationCount(self):
        return self.connectionCount

    def processReservedEvents(self):
        self.signals.imageLoaded.emit(self.image)