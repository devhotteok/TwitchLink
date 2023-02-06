from PyQt5 import QtCore


class ThreadPool(QtCore.QThreadPool):
    def __init__(self, maxThreadCount, parent=None):
        super(ThreadPool, self).__init__(parent=parent)
        self.setMaxThreadCount(maxThreadCount)