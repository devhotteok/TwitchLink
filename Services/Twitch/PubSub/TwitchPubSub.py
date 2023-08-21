from .TwitchPubSubConfig import Config

from Services.Logging.Logger import Logger

from PyQt6 import QtCore, QtNetwork, QtWebSockets

import typing
import json
import secrets


class Topic:
    def __init__(self, eventType: str, targetId: str):
        self.eventType = eventType
        self.targetId = targetId

    @property
    def id(self) -> str:
        return f"{self.eventType}.{self.targetId}"

    def __str__(self):
        return self.id

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other):
        if isinstance(other, Topic):
            return (self.eventType, self.targetId) == (other.eventType, other.targetId)
        else:
            return NotImplemented

    def __ne__(self, other):
        if isinstance(other, Topic):
            return (self.eventType, self.targetId) != (other.eventType, other.targetId)
        else:
            return NotImplemented


class PubSubEvent:
    def __init__(self, topic: Topic, data: dict):
        self.topic = topic
        self.data = data


class PubSubRequest(QtCore.QObject):
    requestTimeout = QtCore.pyqtSignal(object)

    def __init__(self, topics: typing.Iterable[Topic], subscribe: bool, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.topics = topics
        self.nonce = secrets.token_urlsafe(Config.NONCE_LENGTH)
        self.subscribe = subscribe
        self.response = None
        self.timeout = 0
        self._timer = TimeoutTimer(Config.REQUEST_TIMEOUT, self._onTimeout, parent=self)

    def getPayload(self) -> dict:
        return {
            "type": "LISTEN" if self.subscribe else "UNLISTEN",
            "nonce": self.nonce,
            "data": {
                "topics": [
                    topic.id for topic in self.topics
                ]
            }
        }

    def isRetryable(self) -> bool:
        return self.timeout <= Config.REQUEST_TIMEOUT_MAX_RETRY_COUNT

    def _startTimeout(self) -> None:
        self._timer.start()

    def _onTimeout(self) -> None:
        self.timeout += 1
        self.requestTimeout.emit(self)

    def _receive(self, response: dict) -> None:
        self._timer.stop()
        self.response = response

    def __str__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"

    def __repr__(self):
        return self.__str__()


class TimeoutTimer(QtCore.QTimer):
    def __init__(self, timeout: int, callback: typing.Callable, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.setSingleShot(True)
        self.setInterval(timeout)
        self.timeout.connect(callback)


class TwitchPubSubPingPong(QtCore.QObject):
    ping = QtCore.pyqtSignal()
    pingTimeout = QtCore.pyqtSignal()

    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._timer = QtCore.QTimer(parent=self)
        self._timer.setInterval(Config.PING_INTERVAL)
        self._timer.timeout.connect(self._sendPing)
        self._timeoutTimer = TimeoutTimer(Config.PING_TIMEOUT, self._onTimeout, parent=self)

    def _sendPing(self) -> None:
        self._timeoutTimer.start()
        self.ping.emit()

    def _onTimeout(self) -> None:
        self.pingTimeout.emit()

    def pong(self) -> None:
        self._timeoutTimer.stop()

    def start(self) -> None:
        self._sendPing()
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self._timeoutTimer.stop()


class TwitchPubSubWebSocket(QtWebSockets.QWebSocket):
    class ResponseTypes:
        Pong = "PONG"
        Response = "RESPONSE"
        Message = "MESSAGE"
        Reconnect = "RECONNECT"

    def __init__(self, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.logger = logger
        self.pingPong = TwitchPubSubPingPong(parent=self)
        self.pingPong.ping.connect(self.sendTextPing)
        self.pingPong.pingTimeout.connect(self.onPingTimeout)
        self.connected.connect(self.onOpen)
        self.aboutToClose.connect(self.pingPong.stop)
        self.disconnected.connect(self.onClose)
        self.textMessageReceived.connect(self.textMessageHandler)
        self.errorOccurred.connect(self.onError)
        self._reconnectTimer = QtCore.QTimer(parent=self)
        self._reconnectTimer.setSingleShot(True)
        self._reconnectTimer.setInterval(Config.RECONNECT_INTERVAL)
        self._reconnectTimer.timeout.connect(self._reconnectTimerTimeout)
        self._opened = False

    def open(self) -> None:
        self._opened = True
        self.logger.info("[ACTION] WebSocket Open")
        self._connectServer()

    def _connectServer(self) -> None:
        super().open(QtNetwork.QNetworkRequest(QtCore.QUrl(Config.HOST)))

    def close(self) -> None:
        self._opened = False
        self.logger.info("[ACTION] WebSocket Close")
        if self._reconnectTimer.isActive():
            self._reconnectTimer.stop()
        if self.isConnected():
            super().close()

    def isOpened(self) -> bool:
        return self._opened

    def isConnected(self) -> bool:
        return self.isValid()

    def reconnect(self) -> None:
        super().close()

    def sendJsonMessage(self, message: dict) -> None:
        self.sendTextMessage(json.dumps(message))

    def sendTextPing(self) -> None:
        self.sendJsonMessage(
            {
                "type": "PING"
            }
        )
        self.logger.debug("Ping")

    def onPingTimeout(self) -> None:
        self.logger.warning("Ping Timeout")
        self.reconnect()

    def onPong(self) -> None:
        self.pingPong.pong()
        self.logger.debug("Pong")

    def textMessageHandler(self, message: str) -> None:
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
                self.logger.info("Reconnect requested by server.")
                self.reconnect()
            else:
                self.logger.info(f"Unknown Message Data: {responseData}")
        except Exception as e:
            self.logger.error(f"Unable to parse message.\nMessage: {message}")
            self.logger.exception(e)

    def onOpen(self) -> None:
        self.logger.info("WebSocket Connected")
        self.pingPong.start()

    def onResponse(self, response: dict) -> None:
        pass

    def onEvent(self, event: PubSubEvent) -> None:
        pass

    def onClose(self) -> None:
        self.logger.info("WebSocket Closed")
        if self.isOpened():
            self.logger.info("Waiting for connection...")
            self._reconnectTimer.start()

    def onError(self, error: QtNetwork.QAbstractSocket.SocketError) -> None:
        self.logger.error(f"Unexpected Error: {error}")

    def _reconnectTimerTimeout(self) -> None:
        if self.isOpened():
            self.logger.info("Reconnecting...")
            self._connectServer()


class TwitchPubSub(TwitchPubSubWebSocket):
    requestSucceeded = QtCore.pyqtSignal(object)
    requestFailed = QtCore.pyqtSignal(object)
    newEventReceived = QtCore.pyqtSignal(object)

    def __init__(self, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(logger, parent=parent)
        self.pendingRequests = {}
        self.subscribedTopics = []
        self.aboutToClose.connect(self.reset)

    def reset(self) -> None:
        self.pendingRequests.clear()
        self.subscribedTopics.clear()

    def onResponse(self, response: dict) -> None:
        request = self._getRequest(response["nonce"])
        if request != None:
            request._receive(response)
            if response["error"] == "":
                self._onRequestSuccess(request)
            else:
                self._onRequestFailure(request, response["error"])

    def onEvent(self, event: PubSubEvent) -> None:
        self.newEventReceived.emit(event)

    def _sendRequest(self, request: PubSubRequest) -> None:
        if request.nonce not in self.pendingRequests:
            self.pendingRequests[request.nonce] = request
            request.requestTimeout.connect(self._requestTimeout)
        request._startTimeout()
        self.sendJsonMessage(request.getPayload())

    def _requestTimeout(self, request: PubSubRequest) -> None:
        self.logger.info(f"Request Timeout ({request.timeout}/{Config.REQUEST_TIMEOUT_MAX_RETRY_COUNT + 1}): {request}")
        if request.isRetryable():
            self.logger.info("Retrying...")
            self._sendRequest(request)
        else:
            self.reconnect()

    def _onRequestSuccess(self, request: PubSubRequest) -> None:
        self.logger.info(f"Request Success: [{'Subscribe' if request.subscribe else 'Unsubscribe'}] {request.topics}")
        if request.subscribe:
            for topic in request.topics:
                self.subscribedTopics.append(topic)
        else:
            for topic in request.topics:
                self.subscribedTopics.remove(topic)
        self.requestSucceeded.emit(request)

    def _onRequestFailure(self, request: PubSubRequest, errorMessage: str) -> None:
        self.logger.info(f"Request Failed: [{'Subscribe' if request.subscribe else 'Unsubscribe'}] {request.topics}\nError: {errorMessage}")
        self.requestFailed.emit(request)

    def _getRequest(self, nonce: str) -> PubSubRequest | None:
        if nonce in self.pendingRequests:
            return self.pendingRequests.pop(nonce)
        else:
            return None

    def subscribe(self, *topics: Topic) -> PubSubRequest:
        request = PubSubRequest(topics, subscribe=True, parent=None)
        self._sendRequest(request)
        return request

    def unsubscribe(self, *topics: Topic) -> PubSubRequest:
        request = PubSubRequest(topics, subscribe=False, parent=None)
        self._sendRequest(request)
        return request