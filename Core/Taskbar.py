from PyQt5 import QtCore, QtWinExtras


class Taskbar(QtCore.QObject):
    def __init__(self, app, parent=None):
        super(Taskbar, self).__init__(parent=parent)
        self.app = app
        self.taskbarButton = None
        self.taskbarProgress = None

    def reset(self):
        self.taskbarButton = QtWinExtras.QWinTaskbarButton(parent=self)
        self.taskbarButton.setWindow(self.app.mainWindow().windowHandle())
        self.taskbarProgress = self.taskbarButton.progress()

    def show(self, indeterminate=False):
        self.reset()
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
        self.app.alert(self.app.mainWindow())