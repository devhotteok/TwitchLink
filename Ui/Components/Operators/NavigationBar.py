from PyQt5 import QtCore, QtGui


class PageObject(QtCore.QObject):
    showRequested = QtCore.pyqtSignal(object)
    blockRequested = QtCore.pyqtSignal(object)
    unblockRequested = QtCore.pyqtSignal(object)
    focusRequested = QtCore.pyqtSignal(object)
    unfocusRequested = QtCore.pyqtSignal(object)
    buttonShowRequested = QtCore.pyqtSignal(object)
    buttonHideRequested = QtCore.pyqtSignal(object)

    def __init__(self, button, widget, icon=None, parent=None):
        super(PageObject, self).__init__(parent=parent)
        self.button = button
        self.widget = widget
        self.blocked = False
        self.hidden = False
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
        self.showRequested.emit(self)

    def block(self):
        self.blockRequested.emit(self)

    def unblock(self):
        self.unblockRequested.emit(self)

    def focus(self):
        self.focusRequested.emit(self)

    def unfocus(self):
        self.unfocusRequested.emit(self)

    def showButton(self):
        self.buttonShowRequested.emit(self)

    def hideButton(self):
        self.buttonHideRequested.emit(self)


class NavigationBar(QtCore.QObject):
    focusChanged = QtCore.pyqtSignal(bool)

    def __init__(self, stackedWidget, parent=None):
        super(NavigationBar, self).__init__(parent=parent)
        self.stackedWidget = stackedWidget
        self.pages = []
        self.currentPage = None

    def blockPage(self, pageObject):
        pageObject.blocked = True
        pageObject.button.setEnabled(False)
        if self.getCurrentPage() == pageObject:
            for page in self.pages:
                if not page.blocked:
                    self.setCurrentPage(page)
                    return
            self.currentPage = None

    def unblockPage(self, pageObject):
        pageObject.blocked = False
        pageObject.button.setEnabled(True)
        if self.currentPage == None:
            self.setCurrentPage(pageObject)

    def focus(self, pageObject):
        for page in self.pages:
            if page != pageObject:
                self.blockPage(page)
        self.focusChanged.emit(True)

    def unfocus(self):
        for page in self.pages:
            self.unblockPage(page)
        self.focusChanged.emit(False)

    def showPageButton(self, pageObject):
        pageObject.hidden = False
        pageObject.button.show()

    def hidePageButton(self, pageObject):
        pageObject.hidden = True
        pageObject.button.hide()

    def setCurrentPage(self, pageObject):
        if pageObject.blocked:
            return False
        else:
            pageObject.button.setChecked(True)
            self.stackedWidget.setCurrentWidget(pageObject.widget)
            self.currentPage = pageObject
            return True

    def getCurrentPage(self):
        return self.currentPage

    def addPage(self, button, widget, icon=None):
        pageObject = PageObject(button, widget, icon=icon, parent=self)
        pageObject.showRequested.connect(self.setCurrentPage)
        pageObject.blockRequested.connect(self.blockPage)
        pageObject.unblockRequested.connect(self.unblockPage)
        pageObject.focusRequested.connect(self.focus)
        pageObject.unfocusRequested.connect(self.unfocus)
        pageObject.buttonShowRequested.connect(self.showPageButton)
        pageObject.buttonHideRequested.connect(self.hidePageButton)
        self.pages.append(pageObject)
        if self.currentPage == None:
            self.setCurrentPage(pageObject)
        return pageObject