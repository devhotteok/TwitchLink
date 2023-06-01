from Core.Config import Config
from Services.Image.Presets import Icons

from PyQt6 import QtCore, QtGui, QtWidgets


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    clicked = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(SystemTrayIcon, self).__init__(parent=parent)
        self.setIcon(QtGui.QIcon(Icons.APP_LOGO_ICON))
        self.setContextMenu(QtWidgets.QMenu())
        self.activated.connect(self.activatedHandler)
        self.messageClicked.connect(self.messageClickedHandler)
        self.show()
        self.setToolTip(Config.APP_NAME)

    def activatedHandler(self, reason):
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Context:
            return
        self.clicked.emit()

    def messageClickedHandler(self):
        self.clicked.emit()