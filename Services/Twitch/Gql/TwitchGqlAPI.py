from .TwitchGqlModels import *
from .TwitchGqlOperations import *
from .TwitchGqlConfig import Config

from Services.NetworkRequests import Network


class Exceptions:
    class NetworkError(Exception):
        def __init__(self, response):
            if response == None:
                self.status_code = None
                self.data = "Unable to connect to server"
            else:
                self.status_code = response.status_code
                self.data = response.getData()

        def __str__(self):
            return f"Network Error\nstatus_code: {self.status_code}\n{self.data}"

    class ApiError(Exception):
        def __init__(self, data):
            self.data = data

        def __str__(self):
            return f"Twitch API Error\nresponse: {self.data}"

    class DataNotFound(Exception):
        def __str__(self):
            return "Twitch API Error\ndata not found"

class GqlEngine:
    def loadOperations(self, operation, variables):
        return {"query": operation.query, "variables": self.loadVariables(operation.variableList, variables)}

    def loadVariables(self, variableList, variables):
        variablesDict = {}
        for variable in variableList:
            variablesDict[variable] = variables.get(variable)
        return variablesDict

    def api(self, operation, variables, headers=None):
        payload = self.loadOperations(operation, variables)
        try:
            response = Network.session.post(Config.SERVER, headers=headers or {"Client-ID": Config.CLIENT_ID}, json=payload)
        except:
            raise Exceptions.NetworkError(None)
        if response.status_code == 200:
            try:
                json = response.json()
            except:
                raise Exceptions.ApiError(response.getData())
            if "errors" in json:
                raise Exceptions.ApiError(json)
            return json
        else:
            raise Exceptions.NetworkError(response)

class DataList:
    def __init__(self, data, hasNextPage, cursor):
        self.data = data
        self.hasNextPage = hasNextPage
        self.cursor = cursor

class TwitchGqlAPI:
    def __init__(self):
        self._gqlEngine = GqlEngine()

    def _raiseIfNone(self, data, model):
        if data == None:
            raise Exceptions.DataNotFound
        else:
            return model(data)

    def getChannel(self, id="", login="", headers=None):
        if id == "":
            variables = {
                "login": login
            }
        else:
            variables = {
                "id": id
            }
        response = self._gqlEngine.api(getChannel, variables, headers=headers)
        channel = response["data"]["user"]
        return self._raiseIfNone(channel, Channel)

    def getChannelVideos(self, channel, videoType, sort, limit=None, cursor="", headers=None):
        variables = {
            "login": channel,
            "type": videoType,
            "sort": sort,
            "limit": limit or Config.LOAD_LIMIT,
            "cursor": cursor
        }
        response = self._gqlEngine.api(getChannelVideos, variables, headers=headers)
        user = response["data"]["user"]
        if user == None:
            raise Exceptions.DataNotFound
        videos = user["videos"]
        edges = videos["edges"]
        videoList = []
        for data in edges:
            videoList.append(Video(data["node"]))
        hasNextPage = videos["pageInfo"]["hasNextPage"]
        if hasNextPage:
            cursor = edges[-1]["cursor"]
        else:
            cursor = None
        return DataList(videoList, hasNextPage, cursor)

    def getChannelClips(self, channel, filter, limit=None, cursor="", headers=None):
        variables = {
            "login": channel,
            "filter": filter,
            "limit": limit or Config.LOAD_LIMIT,
            "cursor": cursor
        }
        response = self._gqlEngine.api(getChannelClips, variables, headers=headers)
        user = response["data"]["user"]
        if user == None:
            raise Exceptions.DataNotFound
        clips = user["clips"]
        edges = clips["edges"]
        clipList = []
        for data in edges:
            clipList.append(Clip(data["node"]))
        hasNextPage = clips["pageInfo"]["hasNextPage"]
        if hasNextPage:
            cursor = edges[-1]["cursor"]
        else:
            cursor = None
        return DataList(clipList, hasNextPage, cursor)

    def getVideo(self, id, headers=None):
        variables = {
            "id": id
        }
        response = self._gqlEngine.api(getVideo, variables, headers=headers)
        video = response["data"]["video"]
        return self._raiseIfNone(video, Video)

    def getClip(self, slug, headers=None):
        variables = {
            "slug": slug
        }
        response = self._gqlEngine.api(getClip, variables, headers=headers)
        clip = response["data"]["clip"]
        return self._raiseIfNone(clip, Clip)