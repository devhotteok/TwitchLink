from Core import App
from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Services.Document import DocumentData, DocumentButtonData

from PyQt6 import QtCore


class NotificationManager(QtCore.QObject):
    notificationsUpdated = QtCore.pyqtSignal(object)

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.notifications = {}

    def updateNotifications(self, data: dict) -> None:
        updatedNotifications = []
        for notification in data.get(App.Translator.getCurrentLanguageCode(), []):
            targetPlatforms = [item.lower() for item in notification.get("targetPlatforms", [OSUtils.getOSType()])]
            targetVersions = notification.get("targetVersions", [Config.APP_VERSION])
            if OSUtils.getOSType().lower() in targetPlatforms and Config.APP_VERSION in targetVersions:
                documentData = DocumentData(
                    contentId=notification.get("contentId", None),
                    contentVersion=notification.get("contentVersion", 0),
                    title=notification.get("title", ""),
                    content=notification.get("content", ""),
                    contentType=notification.get("contentType", ""),
                    modal=notification.get("modal", False),
                    blockExpiration=notification.get("blockExpiration", False),
                    buttons=[
                        DocumentButtonData(
                            text=button.get("text", ""),
                            action=button.get("action", None),
                            role=button.get("role", "accept"),
                            default=button.get("default", False)
                        ) for button in notification.get("buttons", [])
                    ]
                )
                if self._isNew(documentData):
                    updatedNotifications.append(documentData)
                self.notifications[documentData.contentId] = documentData
        if len(updatedNotifications) != 0:
            self.notificationsUpdated.emit(updatedNotifications)

    def _isNew(self, documentData: DocumentData) -> bool:
        if documentData.contentId in self.notifications:
            if documentData.contentVersion == self.notifications[documentData.contentId].contentVersion:
                return False
        return True

    def isBlocked(self, notification: DocumentData) -> bool:
        return notification.blockExpiration != False and App.Preferences.temp.isContentBlocked(notification.contentId, notification.contentVersion)

    def block(self, notification: DocumentData) -> None:
        App.Preferences.temp.blockContent(notification.contentId, notification.contentVersion, notification.blockExpiration)

    def getNotifications(self) -> list[DocumentData]:
        return list(self.notifications.values())

    def clearAll(self) -> None:
        self.notifications.clear()