from Core.Ui import *
from Services.NotificationManager import NotificationManager
from Ui.Components.Operators.DocumentViewer import DocumentViewer
from Ui.Components.Widgets.TermsOfService import TermsOfService


class InformationPage(DocumentViewer):
    accountRefreshRequested = QtCore.pyqtSignal()
    appShutdownRequested = QtCore.pyqtSignal()

    def __init__(self, pageObject, parent=None):
        super(InformationPage, self).__init__(parent=parent)
        self.pageObject = pageObject
        self.tabCountChanged.connect(self.updatePageState)
        self.updatePageState()
        NotificationManager.notificationsUpdated.connect(self.notificationsUpdated)
        self.notificationsUpdated(NotificationManager.getNotifications())

    def showDocument(self, documentData, icon=None, uniqueValue=None, important=False):
        documentView = Ui.DocumentView(documentData, parent=self)
        super().showDocument(documentView, icon=icon, uniqueValue=uniqueValue, important=important)
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
            super().showDocument(termsOfService, uniqueValue=TermsOfService, important=termsOfService.isEssential())
        else:
            self.setCurrentIndex(tabIndex)
        self.pageObject.show()

    def updatePageState(self):
        if self.isModal():
            self.pageObject.focus()
        else:
            self.pageObject.unfocus()
        if self.count() == 0:
            self.pageObject.hideButton()
            self.pageObject.block()
        else:
            self.pageObject.showButton()
            self.pageObject.unblock()

    def showAppInfo(self, documentData, icon=None):
        return self.showDocument(
            documentData=documentData,
            icon=icon,
            uniqueValue=f"APP_INFO.{documentData.contentId}",
            important=True
        )

    def removeAppInfo(self, contentId):
        tabIndex = self.getUniqueTabIndex(f"APP_INFO.{contentId}")
        if tabIndex != None:
            self.closeTab(tabIndex)

    def notificationsUpdated(self, notifications):
        newIndex = self.count()
        for notification in notifications:
            if not NotificationManager.isBlocked(notification):
                uniqueValue = f"Notification.{notification.contentId}"
                oldVersionIndex = self.getUniqueTabIndex(uniqueValue)
                if oldVersionIndex != None:
                    self.closeTab(oldVersionIndex)
                self.showDocument(notification, icon=None if notification.modal else Icons.NOTICE_ICON, uniqueValue=uniqueValue)
        self.setCurrentIndex(newIndex)