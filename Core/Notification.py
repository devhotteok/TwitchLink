from Services.Image.Presets import Icons

from PyQt6 import QtCore, QtGui, QtWidgets


class Notification(QtCore.QObject):
    class Icons:
        Information = QtWidgets.QSystemTrayIcon.MessageIcon.Information
        Warning = QtWidgets.QSystemTrayIcon.MessageIcon.Warning
        Critical = QtWidgets.QSystemTrayIcon.MessageIcon.Critical

    def __init__(self, parent=None):
        super(Notification, self).__init__(parent=parent)

    #Not Implemented
    def toastMessage(self, title, message, icon=None, actions=None):
        self.parent().systemTray.showMessage(title, message, icon or QtGui.QIcon(Icons.APP_LOGO_ICON))