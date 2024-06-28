from Core.Ui import *


class TabManager(QtWidgets.QTabWidget):
    tabCountChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.setElideMode(QtCore.Qt.TextElideMode.ElideRight)
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.uniqueTabs: dict[typing.Any, QtWidgets.QWidget] = {}
        self._themedTabIcons: dict[QtWidgets.QWidget, ThemedIcon] = {}
        self.tabCloseRequested.connect(self.processTabCloseRequest)
        App.ThemeManager.themeUpdated.connect(self._updateThemedTabIcons)

    def addTab(self, widget: QtWidgets.QWidget, index: int = -1, icon: QtGui.QIcon | ThemedIcon | None = None, closable: bool = True, uniqueValue: typing.Any = None) -> int:
        if uniqueValue != None:
            tabIndex = self.getUniqueTabIndex(uniqueValue)
            if tabIndex != None:
                return tabIndex
            self.uniqueTabs[uniqueValue] = widget
        if isinstance(icon, ThemedIcon):
            self._themedTabIcons[widget] = icon
            tabIcon = icon.icon
        else:
            tabIcon = icon or QtGui.QIcon()
        tabIndex = self.insertTab(index, widget, tabIcon, self.getInjectionSafeText(widget.windowTitle()))
        self.setTabToolTip(tabIndex, widget.windowTitle())
        if not closable:
            self.tabBar().setTabButton(tabIndex, QtWidgets.QTabBar.ButtonPosition.RightSide, None)
        self.tabCountChanged.emit(self.count())
        return tabIndex

    def setTabIcon(self, index: int, icon: QtGui.QIcon | ThemedIcon | None) -> None:
        tabWidget = self.widget(index)
        if isinstance(icon, ThemedIcon):
            self._themedTabIcons[tabWidget] = icon
            tabIcon = icon.icon
        else:
            if tabWidget in self._themedTabIcons:
                self._themedTabIcons.pop(tabWidget)
            tabIcon = icon or QtGui.QIcon()
        super().setTabIcon(index, tabIcon)

    def _updateThemedTabIcons(self) -> None:
        for tabWidget, themedIcon in self._themedTabIcons.items():
            super().setTabIcon(self.indexOf(tabWidget), themedIcon.icon)

    def setTabText(self, index: int, text: str) -> None:
        super().setTabText(index, self.getInjectionSafeText(text))
        self.setTabToolTip(index, text)

    def getInjectionSafeText(self, text: str) -> str:
        return text.replace("&", "&&")

    def getUniqueTabIndex(self, uniqueValue: typing.Any) -> int | None:
        if uniqueValue in self.uniqueTabs:
            return self.indexOf(self.uniqueTabs[uniqueValue])
        else:
            return None

    def closeTab(self, index: int) -> None:
        tabWidget = self.widget(index)
        self.removeTab(index)
        if tabWidget in self._themedTabIcons:
            self._themedTabIcons.pop(tabWidget)
        for key, value in self.uniqueTabs.items():
            if value == tabWidget:
                del self.uniqueTabs[key]
                break
        tabWidget.close()
        self.tabCountChanged.emit(self.count())

    def processTabCloseRequest(self, index: int) -> None:
        self.closeTab(index)

    def closeAllTabs(self) -> None:
        while self.count() != 0:
            self.closeTab(0)