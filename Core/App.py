from Core.Launcher import SingleApplicationLauncher
from Core.Taskbar import Taskbar
from Core.Config import Config

from PyQt5 import QtCore

import sys


class _App(SingleApplicationLauncher):
    appStarted = QtCore.pyqtSignal()

    def __init__(self, guid, argv):
        super(_App, self).__init__(guid, argv)
        self.newInstanceStarted.connect(self.activate)
        self._mainWindow = None
        self.taskbar = None
        self.aboutToQuit.connect(self.cleanup)

    def start(self, window):
        self.setMainWindow(window)
        self.appStarted.emit()
        return self.exec()

    def setMainWindow(self, window):
        self._mainWindow = window
        self.taskbar = Taskbar(self, parent=self)

    def mainWindow(self):
        return self._mainWindow

    def cleanup(self):
        self._mainWindow = None
        self.taskbar = None

    def exit(self, exitCode=0):
        super().exit(exitCode)

    def restart(self):
        self.exit(self.EXIT_CODE.RESTART)

    def activate(self):
        window = self.mainWindow()
        if window != None:
            window.setWindowState((window.windowState() & ~QtCore.Qt.WindowMinimized) | QtCore.Qt.WindowActive)
            window.activateWindow()

App = _App(Config.APP_ROOT, sys.argv)