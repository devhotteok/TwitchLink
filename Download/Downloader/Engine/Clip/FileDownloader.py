from Core.GlobalExceptions import Exceptions
from Services.NetworkRequests import Network
from Services.Task.PrioritizedTask import PrioritizedTask, TaskSignals

from PyQt5 import QtCore


class FileDownloaderSignals(TaskSignals):
    downloadStarted = QtCore.pyqtSignal(int)
    downloadProgress = QtCore.pyqtSignal(int)


class FileDownloader(PrioritizedTask):
    def __init__(self, url, saveAs, priority=0):
        super(FileDownloader, self).__init__(priority=priority, signals=FileDownloaderSignals)
        self.url = url
        self.saveAs = saveAs
        self.stop = False

    def task(self):
        try:
            self.response = Network.session.get(self.url, stream=True, timeout=(10, 60))
            self.response.raise_for_status()
            totalByteSize = int(self.response.headers.get("content-length", 0))
            byteSize = 0
            self.signals.downloadStarted.emit(totalByteSize)
            with open(self.saveAs, "wb") as file:
                for data in self.response.iter_content(1024 ** 2):
                    byteSize += len(data)
                    file.write(data)
                    self.signals.downloadProgress.emit(byteSize)
                    if self.stop:
                        self.tryCloseConnection()
        except Network.Exceptions.RequestException:
            raise Exceptions.NetworkError
        except:
            self.tryCloseConnection()
            raise Exceptions.FileSystemError

    def cancel(self):
        self.stop = True

    def tryCloseConnection(self):
        try:
            self.response.close()
        except:
            pass