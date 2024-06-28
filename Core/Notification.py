from Services.Image.Presets import Icons

from PyQt6 import QtCore, QtGui, QtWidgets


class Notification(QtCore.QObject):
    class Icons:
        Information = QtWidgets.QSystemTrayIcon.MessageIcon.Information
        Warning = QtWidgets.QSystemTrayIcon.MessageIcon.Warning
        Critical = QtWidgets.QSystemTrayIcon.MessageIcon.Critical

    def __init__(self, systemTrayIcon: QtWidgets.QSystemTrayIcon, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.systemTrayIcon = systemTrayIcon

    def toastMessage(self, title: str, message: str, icon: QtWidgets.QSystemTrayIcon.MessageIcon | QtGui.QIcon | None = None) -> None:
        self.systemTrayIcon.showMessage(title, message, icon or Icons.APP_LOGO.icon)