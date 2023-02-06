from Core.App import App
from Services.Twitch.PubSub import TwitchPubSub
from Services.Twitch.PubSub import TwitchPubSubEvents

from PyQt5 import QtCore


class ScheduledDownloadPubSubSubscriber(QtCore.QObject):
    stateChanged = QtCore.pyqtSignal()
    eventReceived = QtCore.pyqtSignal(object)
    removeRequested = QtCore.pyqtSignal(object)

    def __init__(self, channelId, parent):
        super(ScheduledDownloadPubSubSubscriber, self).__init__(parent=parent)
        self.channelId = channelId
        self.topics = (
            TwitchPubSub.Topic(TwitchPubSubEvents.EventTypes.VideoPlaybackById, self.channelId),
            TwitchPubSub.Topic(TwitchPubSubEvents.EventTypes.BroadcastSettingsUpdate, self.channelId)
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

    @property
    def pubSub(self):
        return self.parent().pubSub

    def hasClients(self):
        return len(self._clients) != 0

    def addClient(self, client):
        self._clients.append(client)
        self._update()

    def removeClient(self, client):
        self._clients.remove(client)
        self._update()

    def isSubscribed(self):
        return self._subscribed

    def hasPendingRequest(self):
        return self._pendingRequest != None

    def pubSubConnected(self):
        self._subscribed = False
        self._pendingRequest = None
        self.stateChanged.emit()
        self._update()

    def pubSubDisconnected(self):
        self._subscribed = False
        self._pendingRequest = None
        self.stateChanged.emit()

    def _update(self):
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

    def pubSubRequestSucceeded(self, request):
        if request == self._pendingRequest:
            self._pendingRequest = None
            self._subscribed = request.subscribe
            self.stateChanged.emit()
            self._update()

    def pubSubRequestFailed(self, request):
        if request == self._pendingRequest:
            self._pendingRequest = None
            self.stateChanged.emit()
            self._update()

    def pubSubEventHandler(self, event):
        if event.topic.targetId == self.channelId:
            self.eventReceived.emit(event)


class _ScheduledDownloadPubSub(QtCore.QObject):
    def __init__(self, logger, parent=None):
        super(_ScheduledDownloadPubSub, self).__init__(parent=parent)
        self.pubSub = TwitchPubSub.TwitchPubSub(logger, parent=self)
        self.subscribers = {}

    def open(self):
        self.pubSub.open()

    def close(self):
        self.pubSub.close()

    def isOpened(self):
        return self.pubSub.isOpened()

    def isConnected(self):
        return self.pubSub.isConnected()

    def subscribe(self, channelId, key):
        channelId = str(channelId)
        if channelId not in self.subscribers:
            subscriber = ScheduledDownloadPubSubSubscriber(channelId, parent=self)
            subscriber.removeRequested.connect(self.subscriberRemoveRequested)
            self.subscribers[channelId] = subscriber
        else:
            subscriber = self.subscribers[channelId]
        subscriber.addClient(key)
        return subscriber

    def unsubscribe(self, channelId, key):
        channelId = str(channelId)
        self.subscribers[channelId].removeClient(key)

    def subscriberRemoveRequested(self, subscriber):
        self.subscribers.pop(subscriber.channelId).setParent(None)


ScheduledDownloadPubSub = _ScheduledDownloadPubSub(App.logger)