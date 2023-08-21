from Core.Ui import *
from Services.Document import DocumentData
from Ui.Components.Operators.NavigationBar import PageObject
from Ui.Components.Operators.DocumentViewer import DocumentViewer
from Ui.Components.Widgets.TermsOfService import TermsOfService


class InformationPage(DocumentViewer):
    termsOfServiceAccepted = QtCore.pyqtSignal()
    appShutdownRequested = QtCore.pyqtSignal()

    def __init__(self, pageObject: PageObject, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.pageObject = pageObject
        self.tabCountChanged.connect(self._updatePageState)
        self._updatePageState()
        App.Notifications.notificationsUpdated.connect(self.notificationsUpdated)
        self.notificationsUpdated(App.Notifications.getNotifications())

    def showDocument(self, documentData: DocumentData, icon: str | QtGui.QIcon | None = None, uniqueValue: typing.Any = None, important: bool = False) -> Ui.DocumentView:
        documentView = Ui.DocumentView(documentData, parent=self)
        super().showDocument(documentView, icon=icon, uniqueValue=uniqueValue, important=important)
        self.pageObject.show()
        return documentView

    def openAbout(self) -> None:
        tabIndex = self.getUniqueTabIndex(Ui.About)
        self.setCurrentIndex(self.addTab(Ui.About(parent=self), icon=Icons.INFO_ICON, uniqueValue=Ui.About) if tabIndex == None else tabIndex)
        self.pageObject.show()

    def openTermsOfService(self) -> None:
        tabIndex = self.getUniqueTabIndex(TermsOfService)
        if tabIndex == None:
            termsOfService = TermsOfService(parent=self)
            termsOfService.termsOfServiceAccepted.connect(self.termsOfServiceAccepted)
            termsOfService.appShutdownRequested.connect(self.appShutdownRequested)
            super().showDocument(termsOfService, uniqueValue=TermsOfService, important=termsOfService.isEssential())
        else:
            self.setCurrentIndex(tabIndex)
        self.pageObject.show()

    def _updatePageState(self) -> None:
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

    def showAppInfo(self, documentData: DocumentData, icon: str | QtGui.QIcon | None = None) -> Ui.DocumentView:
        return self.showDocument(
            documentData=documentData,
            icon=icon,
            uniqueValue=f"APP_INFO.{documentData.contentId or ''}",
            important=True
        )

    def removeAppInfo(self, contentId: str) -> None:
        tabIndex = self.getUniqueTabIndex(f"APP_INFO.{contentId}")
        if tabIndex != None:
            self.closeTab(tabIndex)

    def notificationsUpdated(self, notifications: list[DocumentData]) -> None:
        newIndex = self.count()
        for notification in notifications:
            if not App.Notifications.isBlocked(notification):
                uniqueValue = f"Notification.{notification.contentId}"
                oldVersionIndex = self.getUniqueTabIndex(uniqueValue)
                if oldVersionIndex != None:
                    self.closeTab(oldVersionIndex)
                self.showDocument(notification, icon=None if notification.modal else Icons.NOTICE_ICON, uniqueValue=uniqueValue)
        self.setCurrentIndex(newIndex)