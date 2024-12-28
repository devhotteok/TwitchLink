from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Services.Image.Presets import Icons

from PyQt6 import QtCore, QtWidgets


class SystemTrayIcon(QtWidgets.QSystemTrayIcon):
    clicked = QtCore.pyqtSignal()

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.setIcon((Icons.APP_ICON if OSUtils.isWindows() else Icons.APP_ICON_WHITE).icon)
        self.setContextMenu(QtWidgets.QMenu())
        self.activated.connect(self._activatedHandler)
        self.messageClicked.connect(self._messageClickedHandler)
        self.show()
        self.setToolTip(Config.APP_NAME)

    def _activatedHandler(self, reason: QtWidgets.QSystemTrayIcon.ActivationReason) -> None:
        if reason == QtWidgets.QSystemTrayIcon.ActivationReason.Context:
            return
        self.clicked.emit()

    def _messageClickedHandler(self) -> None:
        self.clicked.emit()