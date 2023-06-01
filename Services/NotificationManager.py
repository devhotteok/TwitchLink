from Core.Config import Config
from Services.Translator.Translator import Translator
from Services.Document import DocumentData, DocumentButtonData
from Database.Database import DB

from PyQt6 import QtCore


class _NotificationManager(QtCore.QObject):
    notificationsUpdated = QtCore.pyqtSignal(object)

    def __init__(self, parent=None):
        super(_NotificationManager, self).__init__(parent=parent)
        self.notifications = {}

    def updateNotifications(self, data):
        updatedNotifications = []
        for notification in data.get(Translator.getLanguage(), []):
            if Config.APP_VERSION in notification.get("targetVersion", [Config.APP_VERSION]):
                documentData = DocumentData(
                    contentId=notification.get("contentId", None),
                    contentVersion=notification.get("contentVersion", 0),
                    title=notification.get("title", ""),
                    content=notification.get("content", ""),
                    contentType=notification.get("contentType", ""),
                    modal=notification.get("modal", False),
                    blockExpiry=notification.get("blockExpiry", False),
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

    def _isNew(self, documentData):
        if documentData.contentId in self.notifications:
            if documentData.contentVersion == self.notifications[documentData.contentId].contentVersion:
                return False
        return True

    def isBlocked(self, notification):
        return notification.blockExpiry != False and DB.temp.isContentBlocked(notification.contentId, notification.contentVersion)

    def block(self, notification):
        DB.temp.blockContent(notification.contentId, notification.contentVersion, notification.blockExpiry)

    def getNotifications(self):
        return self.notifications.values()

    def clearAll(self):
        self.notifications = {}

NotificationManager = _NotificationManager()