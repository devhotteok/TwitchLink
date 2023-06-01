from .TwitchPubSubConfig import Config

from PyQt6 import QtCore, QtNetwork, QtWebSockets

import json
import secrets


class PubSubRequest(QtCore.QObject):
    requestTimeout = QtCore.pyqtSignal(object)

    def __init__(self, topics, subscribe, parent=None):
        super(PubSubRequest, self).__init__(parent=parent)
        self.topics = topics
        self.nonce = secrets.token_urlsafe(Config.NONCE_LENGTH)
        self.subscribe = subscribe
        self.response = None
        self.timeout = 0
        self._timer = TimeoutTimer(Config.REQUEST_TIMEOUT, self._onTimeout, parent=self)

    def getPayload(self):
        return {
            "type": "LISTEN" if self.subscribe else "UNLISTEN",
            "nonce": self.nonce,
            "data": {
                "topics": [
                    topic.id for topic in self.topics
                ]
            }
        }

    def isRetryable(self):
        return self.timeout <= Config.REQUEST_TIMEOUT_MAX_RETRY_COUNT

    def _startTimeout(self):
        self._timer.start()

    def _onTimeout(self):
        self.timeout += 1
        self.requestTimeout.emit(self)

    def _receive(self, response):
        self._timer.stop()
        self.response = response

    def __str__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"

    def __repr__(self):
        return self.__str__()


class Topic:
    def __init__(self, eventType, targetId):
        self.eventType = eventType
        self.targetId = targetId

    @property
    def id(self):
        return f"{self.eventType}.{self.targetId}"

    def __str__(self):
        return self.id

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        return self.eventType == other.eventType and self.targetId == other.targetId


class PubSubEvent:
    def __init__(self, topic, data):
        self.topic = topic
        self.data = data


class TimeoutTimer(QtCore.QTimer):
    def __init__(self, timeout, callback, parent=None):
        super().__init__(parent=parent)
        self.setSingleShot(True)
        self.setInterval(timeout)
        self.timeout.connect(callback)


class TwitchPubSubPingPong(QtCore.QObject):
    ping = QtCore.pyqtSignal()
    pingTimeout = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(TwitchPubSubPingPong, self).__init__(parent=parent)
        self._timer = QtCore.QTimer(parent=self)
        self._timer.setInterval(Config.PING_INTERVAL)
        self._timer.timeout.connect(self._sendPing)
        self._timeoutTimer = TimeoutTimer(Config.PING_TIMEOUT, self._onTimeout, parent=self)

    def _sendPing(self):
        self._timeoutTimer.start()
        self.ping.emit()

    def _onTimeout(self):
        self.pingTimeout.emit()

    def pong(self):
        self._timeoutTimer.stop()

    def start(self):
        self._sendPing()
        self._timer.start()

    def stop(self):
        self._timer.stop()
        self._timeoutTimer.stop()


class TwitchPubSubWebSocket(QtWebSockets.QWebSocket):
    class ResponseTypes:
        Pong = "PONG"
        Response = "RESPONSE"
        Message = "MESSAGE"
        Reconnect = "RECONNECT"

    def __init__(self, logger, parent=None):
        super(TwitchPubSubWebSocket, self).__init__(parent=parent)
        self.logger = logger
        self.pingPong = TwitchPubSubPingPong(parent=self)
        self.pingPong.ping.connect(self.sendTextPing)
        self.pingPong.pingTimeout.connect(self.onPingTimeout)
        self.connected.connect(self.onOpen)
        self.aboutToClose.connect(self.pingPong.stop)
        self.disconnected.connect(self.onClose)
        self.textMessageReceived.connect(self.textMessageHandler)
        self.error.connect(self.onError)
        self._opened = False

    def open(self):
        self._opened = True
        self.logger.info("[ACTION] WebSocket Open")
        super().open(QtNetwork.QNetworkRequest(QtCore.QUrl(Config.HOST)))

    def close(self):
        self._opened = False
        self.logger.info("[ACTION] WebSocket Close")
        super().close()

    def isOpened(self):
        return self._opened

    def isConnected(self):
        return self.isValid()

    def reconnect(self):
        super().close()

    def sendJsonMessage(self, jsonMessage):
        self.sendTextMessage(json.dumps(jsonMessage))

    def sendTextPing(self):
        self.sendJsonMessage(
            {
                "type": "PING"
            }
        )
        self.logger.debug("Ping")

    def onPingTimeout(self):
        self.logger.warning("Ping Timeout")
        self.reconnect()

    def onPong(self):
        self.pingPong.pong()
        self.logger.debug("Pong")

    def textMessageHandler(self, message):
        try:
            responseData = json.loads(message)
            responseType = responseData["type"]
            if responseType == self.ResponseTypes.Pong:
                self.onPong()
            elif responseType == self.ResponseTypes.Response:
                self.onResponse(responseData)
            elif responseType == self.ResponseTypes.Message:
                self.onEvent(
                    PubSubEvent(
                        topic=Topic(*responseData["data"]["topic"].split(".", 1)),
                        data=json.loads(responseData["data"]["message"])
                    )
                )
            elif responseType == self.ResponseTypes.Reconnect:
                self.logger.info("Reconnect Requested By Server")
                self.reconnect()
            else:
                self.logger.info(f"Unknown Message Data: {responseData}")
        except Exception as e:
            self.logger.error(f"Unable to parse message.\nMessage: {message}")
            self.logger.exception(e)

    def onOpen(self):
        self.logger.info("WebSocket Connected")
        self.pingPong.start()

    def onResponse(self, response):
        pass

    def onEvent(self, event):
        pass

    def onClose(self):
        self.logger.info("WebSocket Closed")
        if self.isOpened():
            self.logger.info("Reconnecting...")
            self.open()

    def onError(self, error):
        self.logger.error(f"Unexpected Error: {error}")


class TwitchPubSub(TwitchPubSubWebSocket):
    requestSucceeded = QtCore.pyqtSignal(object)
    requestFailed = QtCore.pyqtSignal(object)
    newEventReceived = QtCore.pyqtSignal(object)

    def __init__(self, logger, parent=None):
        super(TwitchPubSub, self).__init__(logger, parent=parent)
        self.aboutToClose.connect(self.reset)
        self.reset()

    def reset(self):
        self.pendingRequests = {}
        self.subscribedTopics = []

    def onResponse(self, response):
        request = self._getRequest(response["nonce"])
        if request != None:
            request._receive(response)
            if response["error"] == "":
                self._onRequestSuccess(request)
            else:
                self._onRequestFailure(request, response["error"])

    def onEvent(self, event):
        self.newEventReceived.emit(event)

    def _sendRequest(self, request):
        if request.nonce not in self.pendingRequests:
            self.pendingRequests[request.nonce] = request
            request.requestTimeout.connect(self._requestTimeout)
        request._startTimeout()
        self.sendJsonMessage(request.getPayload())

    def _requestTimeout(self, request):
        self.logger.info(f"Request Timeout ({request.timeout}/{Config.REQUEST_TIMEOUT_MAX_RETRY_COUNT + 1}): {request}")
        if request.isRetryable():
            self.logger.info("Retrying...")
            self._sendRequest(request)
        else:
            self.reconnect()

    def _onRequestSuccess(self, request):
        self.logger.info(f"Request Success: {request.topics}")
        if request.subscribe:
            for topic in request.topics:
                self.subscribedTopics.append(topic)
        else:
            for topic in request.topics:
                self.subscribedTopics.remove(topic)
        self.requestSucceeded.emit(request)

    def _onRequestFailure(self, request, errorMessage):
        self.logger.info(f"Request Failed: {request.topics}\nError: {errorMessage}")
        self.requestFailed.emit(request)

    def _getRequest(self, nonce):
        if nonce in self.pendingRequests:
            return self.pendingRequests.pop(nonce)
        else:
            return None

    def subscribe(self, *topics):
        request = PubSubRequest(topics, subscribe=True, parent=self)
        self._sendRequest(request)
        return request

    def unsubscribe(self, *topics):
        request = PubSubRequest(topics, subscribe=False, parent=self)
        self._sendRequest(request)
        return request