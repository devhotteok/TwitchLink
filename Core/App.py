from Core.StatusCode import StatusCode

from PyQt5 import QtCore
from PyQt5.QtWinExtras import QWinTaskbarButton


class _Taskbar:
    def __init__(self):
        self.window = None
        self.taskbarButton = None
        self.taskbarProgress = None

    def setWindow(self, window):
        self.window = window
        self.resetTaskbar()

    def clearWindow(self):
        self.window = None

    def resetTaskbar(self):
        self.taskbarButton = QWinTaskbarButton()
        self.taskbarButton.setWindow(self.window.windowHandle())
        self.taskbarProgress = self.taskbarButton.progress()

    def show(self, indeterminate=False):
        self.resetTaskbar()
        if indeterminate:
            self.taskbarProgress.setMaximum(0)
        else:
            self.taskbarProgress.setMaximum(100)
        self.taskbarProgress.show()

    def hide(self):
        self.taskbarProgress.hide()

    def isVisible(self):
        return self.taskbarProgress.isVisible()

    def pause(self):
        if self.taskbarProgress.maximum() == 0:
            self.taskbarProgress.setMaximum(100)
            self.taskbarProgress.setValue(100)
        self.taskbarProgress.pause()

    def isPaused(self):
        return self.taskbarProgress.isPaused()

    def stop(self):
        if self.taskbarProgress.maximum() == 0:
            self.taskbarProgress.setMaximum(100)
            self.taskbarProgress.setValue(100)
        self.taskbarProgress.stop()

    def isStopped(self):
        return self.taskbarProgress.isStopped()

    def resume(self):
        self.taskbarProgress.resume()

    def setValue(self, value):
        if self.isPaused() or self.isStopped():
            self.resume()
        self.taskbarProgress.setValue(value)

    def complete(self):
        self.hide()
        self.alert()

    def alert(self):
        QtCore.QCoreApplication.instance().alert(self.window)

class _App:
    EXIT_CODE = StatusCode

    def __init__(self):
        self._coreWindow = None
        self.taskbar = _Taskbar()

    def start(self, window):
        self.setCoreWindow(window)
        self.coreWindow().start()
        return QtCore.QCoreApplication.exec()

    def setCoreWindow(self, window):
        self._coreWindow = window
        self.taskbar.setWindow(self._coreWindow)

    def coreWindow(self):
        return self._coreWindow

    def deleteCoreWindow(self):
        self._coreWindow = None
        self.taskbar.clearWindow()

    def app(self):
        return QtCore.QCoreApplication.instance()

    def getActiveWindow(self):
        return self.app().activeModalWidget() or self.app().activeWindow() or self.coreWindow()

    def exit(self, exitCode=0):
        self.deleteCoreWindow()
        self.app().exit(exitCode)

    def restart(self):
        self.exit(self.EXIT_CODE.REBOOT)

App = _App()