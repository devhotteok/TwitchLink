from PyQt5 import QtCore


class TaskResult:
    def __init__(self, data=None, error=None):
        self.success = error == None
        self.data = data
        self.error = error


class TaskSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal(object)


class PrioritizedTask(QtCore.QRunnable):
    def __init__(self, priority=0, signals=TaskSignals):
        super(PrioritizedTask, self).__init__()
        self.setAutoDelete(False)
        self.priority = priority
        self.signals = signals()
        self.result = None

    def task(self):
        pass

    def run(self):
        try:
            self.result = TaskResult(data=self.task())
        except Exception as e:
            self.result = TaskResult(error=e)
        self.signals.finished.emit(self)