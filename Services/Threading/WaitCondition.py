from PyQt5 import QtCore


class WaitCondition(QtCore.QObject):
    trueEvent = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(WaitCondition, self).__init__(parent=parent)
        self._mutex = QtCore.QMutex()
        self._locked = False

    def makeTrue(self):
        if self.isFalse():
            self._mutex.unlock()
            self._locked = False
            self.trueEvent.emit()

    def makeFalse(self):
        if self.isTrue():
            self._mutex.lock()
            self._locked = True

    def isTrue(self):
        return not self.isFalse()

    def isFalse(self):
        return self._locked

    def wait(self):
        self._mutex.lock()
        self._mutex.unlock()

    def __del__(self):
        if self._locked:
            self._mutex.unlock()