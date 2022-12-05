from Core.Ui import *


class TabManager(QtWidgets.QTabWidget):
    tabCountChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(TabManager, self).__init__(parent=parent)
        self.setElideMode(QtCore.Qt.TextElideMode.ElideRight)
        self.setDocumentMode(True)
        self.setTabsClosable(True)
        self.setMovable(True)
        self.uniqueTabs = {}
        self.tabCloseRequested.connect(self.processTabCloseRequest)

    def addTab(self, widget, index=-1, icon=QtGui.QIcon(), closable=True, uniqueValue=None):
        if uniqueValue != None:
            tabIndex = self.getUniqueTabIndex(uniqueValue)
            if tabIndex != None:
                return tabIndex
            self.uniqueTabs[uniqueValue] = widget
        tabIndex = self.insertTab(index, widget, icon if isinstance(icon, QtGui.QIcon) else QtGui.QIcon(icon), self.getInjectionSafeText(widget.windowTitle()))
        self.setTabToolTip(tabIndex, widget.windowTitle())
        if not closable:
            self.tabBar().setTabButton(tabIndex, 1, None)
        self.tabCountChanged.emit(self.count())
        return tabIndex

    def setTabIcon(self, index, icon=QtGui.QIcon()):
        return super().setTabIcon(index, icon if isinstance(icon, QtGui.QIcon) else QtGui.QIcon(icon))

    def setTabText(self, index, text):
        super().setTabText(index, self.getInjectionSafeText(text))
        self.setTabToolTip(index, text)

    def getInjectionSafeText(self, text):
        return text.replace("&", "&&")

    def getUniqueTabIndex(self, uniqueValue):
        if uniqueValue in self.uniqueTabs:
            return self.indexOf(self.uniqueTabs[uniqueValue])
        else:
            return None

    def closeTab(self, index):
        widget = self.widget(index)
        self.removeTab(index)
        for key, value in self.uniqueTabs.items():
            if value == widget:
                del self.uniqueTabs[key]
                break
        widget.close()
        self.tabCountChanged.emit(self.count())

    def processTabCloseRequest(self, index):
        self.closeTab(index)

    def closeAllTabs(self):
        while self.count() != 0:
            self.closeTab(0)