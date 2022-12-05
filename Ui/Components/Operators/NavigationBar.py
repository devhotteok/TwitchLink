from PyQt5 import QtCore, QtGui


class PageObject(QtCore.QObject):
    def __init__(self, button, widget, icon=None, parent=None):
        super(PageObject, self).__init__(parent=parent)
        self.button = button
        self.widget = widget
        self.hidden = False
        self.blocked = False
        self.focused = False
        self.button.clicked.connect(self.show)
        if icon != None:
            self.setPageIcon(icon)

    def setPageIcon(self, icon, size=None):
        self.button.setIcon(QtGui.QIcon(icon))
        self.button.setIconSize(size or QtCore.QSize(24, 24))

    def setPageName(self, name):
        self.button.setText(name)
        if name == "":
            self.button.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        else:
            self.button.setToolButtonStyle(QtCore.Qt.ToolButtonTextUnderIcon)

    def show(self):
        self.parent().setCurrentPage(self)

    def showButton(self):
        self.parent().showPageButton(self)

    def hideButton(self):
        self.parent().hidePageButton(self)

    def block(self):
        self.parent().blockPage(self)

    def unblock(self):
        self.parent().unblockPage(self)

    def focus(self):
        self.parent().focus(self)

    def unfocus(self):
        self.parent().unfocus(self)

    def isCurrentPage(self):
        return self.parent().isCurrentPage(self)


class NavigationBar(QtCore.QObject):
    focusChanged = QtCore.pyqtSignal(bool)

    def __init__(self, stackedWidget, parent=None):
        super(NavigationBar, self).__init__(parent=parent)
        self.stackedWidget = stackedWidget
        self.pages = []
        self.currentPage = None

    def showPageButton(self, pageObject):
        if pageObject.hidden:
            pageObject.hidden = False
            pageObject.button.show()

    def hidePageButton(self, pageObject):
        if not pageObject.hidden:
            pageObject.hidden = True
            pageObject.button.hide()

    def blockPage(self, pageObject):
        if not pageObject.blocked:
            pageObject.blocked = True
            self._reload()

    def unblockPage(self, pageObject):
        if pageObject.blocked:
            pageObject.blocked = False
            self._reload()

    def focus(self, pageObject):
        if not pageObject.focused:
            hadFocus = self.hasFocus()
            pageObject.focused = True
            self._reload()
            if hadFocus == False:
                self.focusChanged.emit(True)

    def unfocus(self, pageObject):
        if pageObject.focused:
            pageObject.focused = False
            self._reload()
            if self.hasFocus() == False:
                self.focusChanged.emit(False)

    def setCurrentPage(self, pageObject):
        if pageObject in self.getAvailablePages():
            pageObject.button.setChecked(True)
            self.stackedWidget.setCurrentWidget(pageObject.widget)
            self.currentPage = pageObject
            return True
        else:
            return False

    def getCurrentPage(self):
        return self.currentPage

    def isCurrentPage(self, pageObject):
        return pageObject == self.getCurrentPage()

    def getBlockedPages(self):
        return [pageObject for pageObject in self.pages if pageObject.blocked]

    def getFocusedPages(self):
        return [pageObject for pageObject in self.pages if pageObject.focused]

    def hasFocus(self):
        return len(self.getFocusedPages()) != 0

    def getAvailablePages(self):
        unblockedPages = [pageObject for pageObject in self.pages if not pageObject.blocked]
        return [pageObject for pageObject in unblockedPages if pageObject.focused] or unblockedPages

    def addPage(self, button, widget, icon=None):
        pageObject = PageObject(button, widget, icon=icon, parent=self)
        self.pages.append(pageObject)
        if self.getCurrentPage() == None:
            self.setCurrentPage(pageObject)
        self._reload()
        return pageObject

    def _reload(self):
        availablePages = self.getAvailablePages()
        for pageObject in self.pages:
            pageObject.button.setEnabled(pageObject in availablePages)
        if self.getCurrentPage() not in availablePages:
            if len(availablePages) == 0:
                self.currentPage = None
            else:
                self.setCurrentPage(availablePages[0])