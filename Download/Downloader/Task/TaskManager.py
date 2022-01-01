from .PrioritizedTask import TaskResult

from Services.Utils.MutexLocker import MutexLocker

from PyQt5 import QtCore


class Condition(QtCore.QObject):
    trueEvent = QtCore.pyqtSignal()

    def __init__(self):
        super().__init__()
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


class TaskStatus:
    RUNNING = "running"
    STOP = "stop"
    PAUSE = "pause"

    def __init__(self):
        self._status = TaskStatus.STOP

    def run(self):
        self._status = TaskStatus.RUNNING

    def isRunning(self):
        return self._status == TaskStatus.RUNNING

    def stop(self):
        self._status = TaskStatus.STOP

    def isStopped(self):
        return self._status == TaskStatus.STOP

    def pause(self):
        self._status = TaskStatus.PAUSE

    def isPaused(self):
        return self._status == TaskStatus.PAUSE

class TaskManager(QtCore.QObject):
    taskCompleteSignal = QtCore.pyqtSignal(TaskResult)

    def __init__(self, threadPool):
        super().__init__()
        self.status = TaskStatus()
        self.threadPool = threadPool
        self.tasks = []
        self.runningTasks = []
        self._actionLock = MutexLocker(QtCore.QMutex.Recursive)
        self._pausedCondition = Condition()
        self._doneCondition = Condition()

    def _startTask(self, task):
        self._doneCondition.makeFalse()
        self.threadPool.start(task, priority=task.priority)
        with self._actionLock:
            self.tasks.remove(task)
            self.runningTasks.append(task)

    def _stopTask(self, task):
        stopped = self.threadPool.tryTake(task)
        if stopped:
            with self._actionLock:
                self.runningTasks.remove(task)
                self.tasks.append(task)
        return stopped

    def _taskComplete(self, result):
        with self._actionLock:
            self.runningTasks.remove(result.task)
            if len(self.runningTasks) == 0:
                if self.status.isPaused():
                    self._pausedCondition.makeTrue()
                elif len(self.tasks) == 0:
                    self._doneCondition.makeTrue()
        self.taskCompleteSignal.emit(result)

    @property
    def ifPaused(self):
        return self._pausedCondition.trueEvent

    def isPaused(self):
        return self._pausedCondition.isTrue()

    def waitForPause(self):
        self._pausedCondition.wait()

    @property
    def ifDone(self):
        return self._pausedCondition.trueEvent

    def isDone(self):
        return self._doneCondition.isTrue()

    def waitForDone(self):
        self._doneCondition.wait()

    def add(self, task):
        task.finished.connect(self._taskComplete)
        with self._actionLock:
            self.tasks.append(task)
        if self.status.isRunning():
            self._startTask(task)

    def remove(self, task):
        if not self._stopTask(task):
            with self._actionLock:
                self.tasks.remove(task)

    def resume(self):
        self.status.run()
        self._pausedCondition.makeFalse()
        while len(self.tasks) != 0:
            self._startTask(self.tasks[0])
        if len(self.runningTasks) == 0:
            self._doneCondition.makeTrue()

    def pause(self):
        with self._actionLock:
            self.status.pause()
            i = 0
            while i < len(self.runningTasks):
                if not self._stopTask(self.runningTasks[i]):
                    i += 1
        if len(self.runningTasks) == 0:
            self._pausedCondition.makeTrue()

    def start(self):
        self.resume()

    def stop(self):
        with self._actionLock:
            self.status.stop()
            i = 0
            while i < len(self.runningTasks):
                if not self._stopTask(self.runningTasks[i]):
                    i += 1
            self.tasks = []
        if len(self.runningTasks) == 0:
            self._doneCondition.makeTrue()