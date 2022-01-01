from .Config import Config

from PyQt5 import QtCore


class _ThreadPool(QtCore.QThreadPool):
    def __init__(self, THREAD_LIMIT=None):
        super().__init__()
        self.setMaxThreadCount(THREAD_LIMIT or Config.MAX_THREAD_LIMIT)

ThreadPool = _ThreadPool()