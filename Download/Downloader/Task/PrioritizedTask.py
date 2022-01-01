from PyQt5 import QtCore


class TaskResult:
    def __init__(self, task, result=None, error=None):
        self.task = task
        self.success = error == None
        self.result = result
        self.error = error


class TaskSignals(QtCore.QObject):
    finished = QtCore.pyqtSignal(TaskResult)


class PrioritizedTask(QtCore.QRunnable):
    def __init__(self, target, priority=0):
        super().__init__()
        self.setAutoDelete(False)
        self.target = target
        self.priority = priority
        self.signals = TaskSignals()
        self.finished = self.signals.finished

    def run(self):
        try:
            self.finished.emit(TaskResult(task=self, result=self.target()))
        except Exception as e:
            self.finished.emit(TaskResult(task=self, error=type(e)))