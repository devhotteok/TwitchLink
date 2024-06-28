from PyQt6 import QtGui


class ThemedIcon:
    def __init__(self, lightModePath: str, darkModePath: str):
        self.lightModePath = lightModePath
        self.darkModePath = darkModePath
        self._darkModeEnabled = False
        self._icon: QtGui.QIcon | None = None

    @property
    def icon(self) -> QtGui.QIcon:
        if self._icon == None:
            self._icon = QtGui.QIcon(self.path)
        return self._icon

    @property
    def path(self) -> str:
        return self.darkModePath if self._darkModeEnabled else self.lightModePath

    def setDarkModeEnabled(self, enabled: bool) -> None:
        if self._darkModeEnabled == enabled:
            return
        self._darkModeEnabled = enabled
        newIcon = QtGui.QIcon(self.path)
        if self._icon == None:
            self._icon = newIcon
        else:
            self._icon.swap(newIcon)