from PyQt6 import QtCore


#Not Implemented
class Taskbar(QtCore.QObject):
    def __init__(self, parent=None):
        super(Taskbar, self).__init__(parent=parent)

    def reset(self):
        pass

    def show(self, indeterminate=False):
        pass

    def hide(self):
        pass

    def isVisible(self):
        return False

    def pause(self):
        pass

    def isPaused(self):
        return False

    def stop(self):
        pass

    def isStopped(self):
        return False

    def resume(self):
        pass

    def setValue(self, value):
        pass

    def complete(self):
        pass

    def alert(self):
        pass