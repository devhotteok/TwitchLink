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
        windowTitle = T(widget.windowTitle())
        tabIndex = self.insertTab(index, widget, icon if isinstance(icon, QtGui.QIcon) else QtGui.QIcon(icon), windowTitle)
        self.setTabToolTip(tabIndex, windowTitle)
        if not closable:
            self.tabBar().setTabButton(tabIndex, 1, None)
        self.tabCountChanged.emit(self.count())
        return tabIndex

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