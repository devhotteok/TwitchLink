from . import TwitchGQLModels
from . import TwitchGQLOperations
from .TwitchGQLConfig import Config

from Core import App
from Core import GlobalExceptions
from Services.Twitch.Authentication.Integrity.IntegrityToken import IntegrityToken

from PyQt6 import QtCore, QtNetwork

import typing
import json


class Exceptions(GlobalExceptions.Exceptions):
    class ApiError(Exception):
        def __init__(self, text: str):
            self.text = text

        def __str__(self):
            return f"Twitch API Error\nResponse: {self.text}"

    class IntegrityError(Exception):
        def __str__(self):
            return f"Integrity Error"

    class AuthorizationError(Exception):
        def __str__(self):
            return "Authorization Error"

    class DataNotFound(Exception):
        def __str__(self):
            return "Twitch API Error\nData Not Found"


class TwitchGQLResponse(QtCore.QObject):
    finished = QtCore.pyqtSignal(object)

    def __init__(self, payload: str, parser: typing.Callable[[dict], TwitchGQLModels.TwitchGQLObject], useIntegrity: bool = False, useAuth: bool = False, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._payload = payload
        self._parser = parser
        self._useIntegrity = useIntegrity
        self._useAuth = useAuth
        self._reply: QtNetwork.QNetworkReply | None = None
        self._error: Exception | None = None
        self._data: TwitchGQLModels.TwitchGQLObject | None = None
        if self._useIntegrity:
            App.Account.getIntegrityToken(self._integrityTokenGenerated)
        else:
            self._startRequest()

    def _integrityTokenGenerated(self, integrityToken: IntegrityToken | None) -> None:
        self._startRequest(None if integrityToken == None else integrityToken.getHeaders())

    def _startRequest(self, headers: dict | None = None) -> None:
        if headers == None:
            headers = {"Client-ID": Config.CLIENT_ID}
        if self._useAuth:
            headers.update({"Authorization": f"OAuth {App.Account.getOAuthToken()}"})
        request = QtNetwork.QNetworkRequest(QtCore.QUrl(Config.SERVER))
        for key, value in headers.items():
            request.setRawHeader(key.encode(), value.encode())
        request.setHeader(QtNetwork.QNetworkRequest.KnownHeaders.ContentTypeHeader, "application/json")
        self._reply = App.NetworkAccessManager.post(request, self._payload.encode())
        self._reply.finished.connect(self._replyFinished)

    def _replyFinished(self) -> None:
        if self._reply.error() == QtNetwork.QNetworkReply.NetworkError.NoError:
            text = self._reply.readAll().data().decode()
            try:
                jsonData = json.loads(text)
            except:
                self._raiseException(Exceptions.ApiError(text))
            else:
                try:
                    self._data = self._parseData(jsonData)
                    self._setFinished()
                except Exceptions.IntegrityError as e:
                    App.Account.updateIntegrityToken()
                    self._raiseException(e)
                except:
                    self._raiseException(Exceptions.ApiError(text))
        elif self._reply.error() == QtNetwork.QNetworkReply.NetworkError.AuthenticationRequiredError:
            self._raiseException(Exceptions.AuthorizationError())
        else:
            self._raiseException(Exceptions.NetworkError(self._reply))

    def _parseData(self, data: dict) -> TwitchGQLModels.TwitchGQLObject:
        if "errors" in data:
            for error in data["errors"]:
                if error.get("message") == "failed integrity check":
                    raise Exceptions.IntegrityError
        return self._parser(data)

    def _setFinished(self) -> None:
        self.finished.emit(self)
        self.deleteLater()

    def _raiseException(self, exception: Exception) -> None:
        self._error = exception
        self._setFinished()

    def getError(self) -> Exception:
        return self._error

    def getData(self) -> TwitchGQLModels.TwitchGQLObject:
        return self._data


class DataList(TwitchGQLModels.TwitchGQLObject):
    def __init__(self, data: list[TwitchGQLModels.TwitchGQLObject], hasNextPage: bool, cursor: str | None):
        self.data = data
        self.hasNextPage = hasNextPage
        self.cursor = cursor


class TwitchGQL(QtCore.QObject):
    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)

    def _send(self, operation: typing.Type[TwitchGQLOperations.TwitchGQLOperation], variables: dict, parser: typing.Callable[[dict], TwitchGQLModels.TwitchGQLObject]) -> TwitchGQLResponse:
        useIntegrity = operation in (TwitchGQLOperations.GetChannelVideos, TwitchGQLOperations.GetChannelClips)
        return self._sendPayload(operation.load(variables), parser, useIntegrity=useIntegrity, useAuth=False)

    def _sendPayload(self, payload: dict, parser: typing.Callable[[dict], TwitchGQLModels.TwitchGQLObject], useIntegrity: bool = False, useAuth: bool = False) -> TwitchGQLResponse:
        return TwitchGQLResponse(json.dumps(payload), parser, useIntegrity=useIntegrity, useAuth=useAuth, parent=self)

    @staticmethod
    def _raiseIfNone(data: dict | None, model: typing.Type[TwitchGQLModels.TwitchGQLObject]) -> TwitchGQLModels.TwitchGQLObject:
        if data == None:
            raise Exceptions.DataNotFound
        elif int(data.get("id") or 0) == 0:
            raise Exceptions.DataNotFound
        else:
            return model(data)

    def getChannel(self, id: str = "", login: str = "") -> TwitchGQLResponse:
        if id == "":
            variables = {
                "login": login
            }
        else:
            variables = {
                "id": id
            }
        return self._send(
            operation=TwitchGQLOperations.GetChannel,
            variables=variables,
            parser=self._channelParser
        )

    def _channelParser(self, response: dict) -> TwitchGQLModels.TwitchGQLObject:
        channel = response["data"]["user"]
        return self._raiseIfNone(channel, TwitchGQLModels.Channel)

    def getChannelVideos(self, channel: str, videoType: str, sort: str, limit: int | None = None, cursor: str | None = None) -> TwitchGQLResponse:
        variables = {
            "login": channel,
            "type": videoType,
            "sort": sort,
            "limit": limit or Config.LOAD_LIMIT,
            "cursor": cursor or ""
        }
        return self._send(
            operation=TwitchGQLOperations.GetChannelVideos,
            variables=variables,
            parser=self._channelVideosParser
        )

    def _channelVideosParser(self, response: dict) -> TwitchGQLModels.TwitchGQLObject:
        user = response["data"]["user"]
        if user == None:
            raise Exceptions.DataNotFound
        videos = user["videos"]
        edges = videos["edges"]
        videoList = []
        for data in edges:
            videoList.append(TwitchGQLModels.Video(data["node"]))
        hasNextPage = videos["pageInfo"]["hasNextPage"]
        if hasNextPage:
            cursor = edges[-1]["cursor"]
        else:
            cursor = None
        return DataList(videoList, hasNextPage, cursor)

    def getChannelClips(self, channel: str, filter: str, limit: int | None = None, cursor: str | None = None) -> TwitchGQLResponse:
        variables = {
            "login": channel,
            "filter": filter,
            "limit": limit or Config.LOAD_LIMIT,
            "cursor": cursor or ""
        }
        return self._send(
            operation=TwitchGQLOperations.GetChannelClips,
            variables=variables,
            parser=self._channelClipsParser
        )

    def _channelClipsParser(self, response: dict) -> TwitchGQLModels.TwitchGQLObject:
        user = response["data"]["user"]
        if user == None:
            raise Exceptions.DataNotFound
        clips = user["clips"]
        edges = clips["edges"]
        clipList = []
        for data in edges:
            clipList.append(TwitchGQLModels.Clip(data["node"]))
        hasNextPage = clips["pageInfo"]["hasNextPage"]
        if hasNextPage:
            cursor = edges[-1]["cursor"]
        else:
            cursor = None
        return DataList(clipList, hasNextPage, cursor)

    def getVideo(self, id: str) -> TwitchGQLResponse:
        variables = {
            "id": id
        }
        return self._send(
            operation=TwitchGQLOperations.GetVideo,
            variables=variables,
            parser=self._videoParser
        )

    def _videoParser(self, response: dict) -> TwitchGQLModels.TwitchGQLObject:
        video = response["data"]["video"]
        return self._raiseIfNone(video, TwitchGQLModels.Video)

    def getClip(self, slug: str) -> TwitchGQLResponse:
        variables = {
            "slug": slug
        }
        return self._send(
            operation=TwitchGQLOperations.GetClip,
            variables=variables,
            parser=self._clipParser
        )

    def _clipParser(self, response: dict) -> TwitchGQLModels.TwitchGQLObject:
        clip = response["data"]["clip"]
        return self._raiseIfNone(clip, TwitchGQLModels.Clip)

    def getStreamPlaybackAccessToken(self, login: str) -> TwitchGQLResponse:
        return self._sendPayload(
            payload={
                "operationName": Config.STREAM_PLAYBACK_ACCESS_TOKEN_OPERATOR[0],
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": Config.STREAM_PLAYBACK_ACCESS_TOKEN_OPERATOR[1]
                    }
                },
                "variables": {
                    "isLive": True,
                    "login": login,
                    "isVod": False,
                    "vodID": "",
                    "playerType": "embed"
                }
            },
            parser=self._streamPlaybackAccessTokenParser,
            useIntegrity=True,
            useAuth=True
        )

    def _streamPlaybackAccessTokenParser(self, response: dict) -> TwitchGQLModels.TwitchGQLObject:
        data = response["data"]["streamPlaybackAccessToken"]
        if data == None:
            raise Exceptions.DataNotFound
        return TwitchGQLModels.StreamPlaybackAccessToken(data)

    def getVideoPlaybackAccessToken(self, id: str) -> TwitchGQLResponse:
        return self._sendPayload(
            payload={
                "operationName": Config.VIDEO_PLAYBACK_ACCESS_TOKEN_TOKEN_OPERATOR[0],
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": Config.VIDEO_PLAYBACK_ACCESS_TOKEN_TOKEN_OPERATOR[1]
                    }
                },
                "variables": {
                    "isLive": False,
                    "login": "",
                    "isVod": True,
                    "vodID": id,
                    "playerType": "embed"
                }
            },
            parser=self._videoPlaybackAccessTokenParser,
            useIntegrity=True,
            useAuth=True
        )

    def _videoPlaybackAccessTokenParser(self, response: dict) -> TwitchGQLModels.TwitchGQLObject:
        data = response["data"]["videoPlaybackAccessToken"]
        if data == None:
            raise Exceptions.DataNotFound
        return TwitchGQLModels.VideoPlaybackAccessToken(data)

    def getClipPlaybackAccessToken(self, slug: str) -> TwitchGQLResponse:
        return self._sendPayload(
            payload={
                "operationName": Config.CLIP_PLAYBACK_ACCESS_TOKEN_TOKEN_OPERATOR[0],
                "extensions": {
                    "persistedQuery": {
                        "version": 1,
                        "sha256Hash": Config.CLIP_PLAYBACK_ACCESS_TOKEN_TOKEN_OPERATOR[1]
                    }
                },
                "variables": {
                    "slug": slug
                }
            },
            parser=self._clipPlaybackAccessTokenParser,
            useIntegrity=True,
            useAuth=True
        )

    def _clipPlaybackAccessTokenParser(self, response: dict) -> TwitchGQLModels.TwitchGQLObject:
        data = response["data"]["clip"]
        if data == None:
            raise Exceptions.DataNotFound
        return TwitchGQLModels.ClipPlaybackAccessToken(data)