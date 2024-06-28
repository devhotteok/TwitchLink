from .ThemedIcon import ThemedIcon

from Core.App import ThemeManager

from PyQt6 import QtCore, QtGui, QtWidgets


class ThemedIconViewer(QtCore.QObject):
    def __init__(self, widget: QtWidgets.QPushButton | QtWidgets.QToolButton, themedIcon: QtGui.QIcon | ThemedIcon | None):
        self.widget = widget
        self.themedIcon = themedIcon
        super().__init__(parent=self.widget)
        ThemeManager.themeUpdated.connect(self._loadIcon)
        self._loadIcon()

    def setIcon(self, themedIcon: QtGui.QIcon | ThemedIcon | None) -> None:
        self.themedIcon = themedIcon
        self._loadIcon()

    def _getIconObject(self) -> QtGui.QIcon:
        if isinstance(self.themedIcon, QtGui.QIcon):
            return self.themedIcon
        elif isinstance(self.themedIcon, ThemedIcon):
            return self.themedIcon.icon
        else:
            return QtGui.QIcon()

    def _loadIcon(self) -> None:
        if isinstance(self.widget, QtWidgets.QPushButton):
            self.widget.setIcon(self._getIconObject())
        elif isinstance(self.widget, QtWidgets.QToolButton):
            self.widget.setIcon(self._getIconObject())