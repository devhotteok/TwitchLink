from .ThemedIcon import ThemedIcon

from Core.App import ThemeManager

from PyQt6 import QtWidgets, QtSvgWidgets


class ThemedSvgWidget(QtSvgWidgets.QSvgWidget):
    def __init__(self, themedIcon: str | ThemedIcon, parent: QtWidgets.QWidget | None = None):
        self.themedIcon = themedIcon
        super().__init__(self.themedIcon.path, parent=parent)
        ThemeManager.themeUpdated.connect(self._loadIcon)

    def setIcon(self, themedIcon: str | ThemedIcon) -> None:
        self.themedIcon = themedIcon
        self._loadIcon()

    def _loadIcon(self) -> None:
        if isinstance(self.themedIcon, str):
            self.load(self.themedIcon)
        else:
            self.load(self.themedIcon.path)