from PyQt5 import QtCore


class WorkerThreadResult:
    def __init__(self, data=None, error=None):
        self.success = error == None
        self.data = data
        self.error = error


class WorkerThread(QtCore.QThread):
    resultSignal = QtCore.pyqtSignal(WorkerThreadResult)

    def __init__(self, target=lambda: None, args=None, kwargs=None):
        super().__init__()
        self.target = target
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.result = None

    def run(self):
        try:
            self.result = WorkerThreadResult(data=self.target(*self.args, **self.kwargs))
        except Exception as e:
            self.result = WorkerThreadResult(error=type(e))
        self.resultSignal.emit(self.result)