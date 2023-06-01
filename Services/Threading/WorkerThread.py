from PyQt6 import QtCore


class WorkerThreadResult:
    def __init__(self, data=None, error=None):
        self.success = error == None
        self.data = data
        self.error = error


class WorkerThread(QtCore.QThread):
    resultSignal = QtCore.pyqtSignal(WorkerThreadResult)

    def __init__(self, target=None, args=None, kwargs=None, parent=None):
        super(WorkerThread, self).__init__(parent=parent)
        self.setup(target, args, kwargs)

    def setup(self, target=None, args=None, kwargs=None, disconnect=False):
        if self.isRunning():
            return False
        else:
            self.target = target
            self.args = args or ()
            self.kwargs = kwargs or {}
            self.result = None
            if disconnect:
                try:
                    self.resultSignal.disconnect()
                except:
                    pass
            return True

    def run(self):
        try:
            self.result = WorkerThreadResult(data=None if self.target == None else self.target(*self.args, **self.kwargs))
        except Exception as e:
            self.result = WorkerThreadResult(error=e)
        self.resultSignal.emit(self.result)