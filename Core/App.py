from Core.Launcher import SingleApplicationLauncher
from Core.Taskbar import Taskbar
from Core.SystemTrayIcon import SystemTrayIcon
from Core.Notification import Notification
from Core.Config import Config

from PyQt6 import QtCore

import sys


class _App(SingleApplicationLauncher):
    appStarted = QtCore.pyqtSignal()

    def __init__(self, guid, argv):
        super(_App, self).__init__(guid, argv)
        self.taskbar = Taskbar(parent=self)
        self.systemTray = SystemTrayIcon(parent=self)
        self.notification = Notification(parent=self)

    def start(self, mainWindow):
        self.appStarted.emit()
        return self.exec()

    def exit(self, exitCode=0):
        super().exit(exitCode)

    def restart(self):
        self.exit(self.EXIT_CODE.RESTART)

App = _App(Config.APP_ROOT, sys.argv)