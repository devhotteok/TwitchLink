from .Palette import Palette
from .ThemedIconManager import ThemedIconManager

from Core import App
from Services.Utils.OSUtils import OSUtils

from PyQt6 import QtCore, QtGui

import typing
import enum


class ThemeManager(QtCore.QObject):
    themeUpdated = QtCore.pyqtSignal()

    class Modes(enum.Enum):
        AUTO = ""
        LIGHT = "light"
        DARK = "dark"

        def isAuto(self) -> bool:
            return self == self.AUTO

        def isLight(self) -> bool:
            return self == self.LIGHT

        def isDark(self) -> bool:
            return self == self.DARK

        def toString(self) -> str:
            return self.value

        @classmethod
        def fromString(cls, value: str) -> typing.Self | None:
            for member in cls:
                if member.value == value:
                    return member
            return None


    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._themeMode: ThemeManager.Modes = self.Modes.AUTO
        App.Instance.styleHints().colorSchemeChanged.connect(self._colorSchemeChanged)

    def getThemeMode(self) -> Modes:
        return self._themeMode

    def setThemeMode(self, themeMode: Modes) -> None:
        self._themeMode = themeMode
        self.updateTheme()

    def isDarkModeEnabled(self) -> bool:
        return self._themeMode.isDark() or (self._themeMode.isAuto() and App.Instance.styleHints().colorScheme() == QtCore.Qt.ColorScheme.Dark)

    def _colorSchemeChanged(self, colorScheme: QtCore.Qt.ColorScheme) -> None:
        self.updateTheme()

    def updateTheme(self) -> None:
        ThemedIconManager.setDarkModeEnabled(self.isDarkModeEnabled())
        palette = QtGui.QPalette()
        paletteData = Palette.DARK if self.isDarkModeEnabled() else Palette.LIGHT
        for role, roleData in paletteData.items():
            for group, color in roleData.items():
                palette.setColor(group, role, QtGui.QColor(*color))
        App.Instance.setPalette(palette)
        App.Instance.setStyle(OSUtils.getDarkStyle() if self.isDarkModeEnabled() else OSUtils.getLightStyle())
        self.themeUpdated.emit()