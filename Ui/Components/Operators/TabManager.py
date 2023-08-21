from Core.Ui import *


class TabManager(QtWidgets.QTabWidget):
    tabCountChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.setElideMode(QtCore.Qt.TextElideMode.ElideRight)
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.uniqueTabs = {}
        self.tabCloseRequested.connect(self.processTabCloseRequest)

    def addTab(self, widget: QtWidgets.QWidget, index: int = -1, icon: str | QtGui.QIcon = "", closable: bool = True, uniqueValue: typing.Any = None) -> int:
        if uniqueValue != None:
            tabIndex = self.getUniqueTabIndex(uniqueValue)
            if tabIndex != None:
                return tabIndex
            self.uniqueTabs[uniqueValue] = widget
        tabIndex = self.insertTab(index, widget, icon if isinstance(icon, QtGui.QIcon) else QtGui.QIcon(icon), self.getInjectionSafeText(widget.windowTitle()))
        self.setTabToolTip(tabIndex, widget.windowTitle())
        if not closable:
            self.tabBar().setTabButton(tabIndex, QtWidgets.QTabBar.ButtonPosition.RightSide, None)
        self.tabCountChanged.emit(self.count())
        return tabIndex

    def setTabIcon(self, index: int, icon: str | QtGui.QIcon) -> None:
        super().setTabIcon(index, icon if isinstance(icon, QtGui.QIcon) else QtGui.QIcon(icon))

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
        widget = self.widget(index)
        self.removeTab(index)
        for key, value in self.uniqueTabs.items():
            if value == widget:
                del self.uniqueTabs[key]
                break
        widget.close()
        self.tabCountChanged.emit(self.count())

    def processTabCloseRequest(self, index: int) -> None:
        self.closeTab(index)

    def closeAllTabs(self) -> None:
        while self.count() != 0:
            self.closeTab(0)