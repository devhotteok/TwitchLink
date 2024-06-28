from .ThemedIcon import ThemedIcon


class ThemedIconManager:
    icons: list[ThemedIcon] = []
    darkModeEnabled: bool = False

    @classmethod
    def create(cls, lightModePath: str, darkModePath: str) -> ThemedIcon:
        themedIcon = ThemedIcon(lightModePath, darkModePath)
        cls.icons.append(themedIcon)
        return themedIcon

    @classmethod
    def remove(cls, themedIcon: ThemedIcon) -> None:
        if themedIcon in cls.icons:
            cls.icons.remove(themedIcon)

    @classmethod
    def setDarkModeEnabled(cls, enabled: bool) -> None:
        if cls.darkModeEnabled == enabled:
            return
        cls.darkModeEnabled = enabled
        for themedIcon in cls.icons:
            themedIcon.setDarkModeEnabled(cls.darkModeEnabled)