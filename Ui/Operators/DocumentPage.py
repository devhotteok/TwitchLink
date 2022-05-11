from Core.Ui import *
from Ui.Operators.DocumentViewer import DocumentViewer
from Ui.Operators.TermsOfService import TermsOfService


class DocumentPage(DocumentViewer):
    accountRefreshRequested = QtCore.pyqtSignal()
    appShutdownRequested = QtCore.pyqtSignal()

    def __init__(self, pageObject, parent=None):
        super(DocumentPage, self).__init__(parent=parent)
        self.pageObject = pageObject
        self.tabCountChanged.connect(self.updatePageState)
        self.updatePageState()

    def showDocument(self, documentData, icon=None, uniqueValue=None):
        documentView = Ui.DocumentView(documentData, parent=self)
        super().showDocument(documentView, icon=icon, uniqueValue=uniqueValue)
        self.pageObject.show()
        return documentView

    def openAbout(self):
        tabIndex = self.getUniqueTabIndex(Ui.About)
        self.setCurrentIndex(self.addTab(Ui.About(parent=self), icon=Icons.INFO_ICON, uniqueValue=Ui.About) if tabIndex == None else tabIndex)
        self.pageObject.show()

    def openTermsOfService(self):
        tabIndex = self.getUniqueTabIndex(TermsOfService)
        if tabIndex == None:
            termsOfService = TermsOfService(parent=self)
            termsOfService.termsOfServiceAccepted.connect(self.accountRefreshRequested)
            termsOfService.appShutdownRequested.connect(self.appShutdownRequested)
            super().showDocument(termsOfService, uniqueValue=TermsOfService)
        else:
            self.setCurrentIndex(tabIndex)
        self.pageObject.show()

    def updatePageState(self):
        if self.isModal():
            self.pageObject.focus()
        else:
            self.pageObject.unfocus()
        if self.count() == 0:
            self.pageObject.block()
            self.pageObject.hideButton()
        else:
            self.pageObject.unblock()
            self.pageObject.showButton()