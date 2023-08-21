from Services.Logging.Logger import Logger
from Services.Twitch.PubSub import TwitchPubSub
from Services.Twitch.PubSub.TwitchPubSubEvents import EventTypes

from PyQt6 import QtCore

import uuid


class ScheduledDownloadPubSubSubscriber(QtCore.QObject):
    stateChanged = QtCore.pyqtSignal()
    eventReceived = QtCore.pyqtSignal(object)
    removeRequested = QtCore.pyqtSignal(object)

    def __init__(self, channelId: str, pubSub: TwitchPubSub.TwitchPubSub, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.channelId = channelId
        self.pubSub = pubSub
        self.topics = (
            TwitchPubSub.Topic(EventTypes.VideoPlaybackById, self.channelId),
            TwitchPubSub.Topic(EventTypes.BroadcastSettingsUpdate, self.channelId)
        )
        self._subscribed = False
        self._pendingRequest = None
        self._clients = []
        self.pubSub.connected.connect(self.pubSubConnected)
        self.pubSub.disconnected.connect(self.pubSubDisconnected)
        self.pubSub.requestSucceeded.connect(self.pubSubRequestSucceeded)
        self.pubSub.requestFailed.connect(self.pubSubRequestFailed)
        self.pubSub.newEventReceived.connect(self.pubSubEventHandler)
        if self.pubSub.isConnected():
            self.pubSubConnected()

    def hasClients(self) -> bool:
        return len(self._clients) != 0

    def addClient(self, client: uuid.UUID) -> None:
        self._clients.append(client)
        self._update()

    def removeClient(self, client: uuid.UUID) -> None:
        self._clients.remove(client)
        self._update()

    def isSubscribed(self) -> bool:
        return self._subscribed

    def hasPendingRequest(self) -> bool:
        return self._pendingRequest != None

    def pubSubConnected(self) -> None:
        self._subscribed = False
        self._pendingRequest = None
        self.stateChanged.emit()
        self._update()

    def pubSubDisconnected(self) -> None:
        self._subscribed = False
        self._pendingRequest = None
        self.stateChanged.emit()

    def _update(self) -> None:
        if self.pubSub.isConnected():
            if self._pendingRequest == None:
                if self.hasClients() and not self.isSubscribed():
                    self._pendingRequest = self.pubSub.subscribe(*self.topics)
                    self.stateChanged.emit()
                elif not self.hasClients() and self.isSubscribed():
                    self._pendingRequest = self.pubSub.unsubscribe(*self.topics)
                    self.stateChanged.emit()
                elif not self.hasClients() and not self.isSubscribed():
                    self.removeRequested.emit(self)

    def pubSubRequestSucceeded(self, request: TwitchPubSub.PubSubRequest) -> None:
        if request == self._pendingRequest:
            self._pendingRequest = None
            self._subscribed = request.subscribe
            self.stateChanged.emit()
            self._update()

    def pubSubRequestFailed(self, request: TwitchPubSub.PubSubRequest) -> None:
        if request == self._pendingRequest:
            self._pendingRequest = None
            self.stateChanged.emit()
            self._update()

    def pubSubEventHandler(self, event: TwitchPubSub.PubSubEvent) -> None:
        if event.topic.targetId == self.channelId:
            self.eventReceived.emit(event)


class ScheduledDownloadPubSubManager(QtCore.QObject):
    def __init__(self, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.pubSub = TwitchPubSub.TwitchPubSub(logger, parent=self)
        self.subscribers = {}

    def open(self) -> None:
        self.pubSub.open()

    def close(self) -> None:
        self.pubSub.close()

    def isOpened(self) -> bool:
        return self.pubSub.isOpened()

    def isConnected(self) -> bool:
        return self.pubSub.isConnected()

    def subscribe(self, channelId: str, key: uuid.UUID) -> ScheduledDownloadPubSubSubscriber:
        if channelId not in self.subscribers:
            subscriber = ScheduledDownloadPubSubSubscriber(channelId, self.pubSub, parent=self)
            subscriber.removeRequested.connect(self.subscriberRemoveRequested)
            self.subscribers[channelId] = subscriber
        else:
            subscriber = self.subscribers[channelId]
        subscriber.addClient(key)
        return subscriber

    def unsubscribe(self, channelId: str, key: uuid.UUID) -> None:
        self.subscribers[channelId].removeClient(key)

    def subscriberRemoveRequested(self, subscriber: ScheduledDownloadPubSubSubscriber) -> None:
        self.subscribers.pop(subscriber.channelId).deleteLater()