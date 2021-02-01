import requests

from Services.Twitch.TwitchGqlModels import *
from Services.Twitch.TwitchGqlOperations import *


class NetworkError(Exception):
    def __init__(self, response):
        self.status_code = response.status_code
        self.json = response.json()

    def __str__(self):
        return "\nNetwork Error\nstatus_code : " + str(self.status_code) + "\n" + str(self.json)

class ApiError(Exception):
    def __init__(self, json):
        self.json = json

    def __str__(self):
        return "\nTwitch Error\nresponse : " + str(self.json)

class DataNotFound(Exception):
    def __str__(self):
        return "\nTwitch Error\ndata not found"

class Gql:
    def __init__(self):
        self.CLIENT_ID = "kimne78kx3ncx6brgo4mv6wki5h1ko"
        self.headers = {"Client-ID": self.CLIENT_ID}

    def loadOperations(self, operation, variables):
        return {"query": operation.query, "variables": self.loadVariables(operation.variableList, variables)}

    def loadVariables(self, variableList, variables):
        variablesDict = {}
        for variable in variableList:
            variablesDict[variable] = variables.get(variable)
        return variablesDict

    def api(self, operation, variables):
        payload = self.loadOperations(operation, variables)
        response = requests.post("https://gql.twitch.tv/gql", headers=self.headers, json=payload)
        if response.status_code == 200:
            json = response.json()
            if "errors" in json:
                raise ApiError(json)
            return response.json()
        else:
            raise NetworkError(response)

class ModelList:
    def __init__(self, data, hasNextPage, cursor):
        self.data = data
        self.hasNextPage = hasNextPage
        self.cursor = cursor

class TwitchGqlAPI:
    def __init__(self):
        self.gql = Gql()

    def errorIfNone(self, data, model):
        if data == None:
            raise DataNotFound
        else:
            return model(data)

    def getChannel(self, channel):
        variables = {
            "login": channel,
            "channelLogin": channel,
        }
        response = self.gql.api(getChannel, variables)
        channel = response["data"]["user"]
        return self.errorIfNone(channel, Channel)

    def getChannelVideos(self, channel, type, sort, limit=100, cursor=""):
        variables = {
            "login": channel,
            "type": type,
            "sort": sort,
            "limit": limit,
            "cursor": cursor
        }
        response = self.gql.api(getChannelVideos, variables)
        videos = response["data"]["user"]["videos"]
        edges = videos["edges"]
        videoList = []
        for data in edges:
            videoList.append(Video(data["node"]))
        hasNextPage = videos["pageInfo"]["hasNextPage"]
        if hasNextPage:
            cursor = edges[-1]["cursor"]
        else:
            cursor = None
        return ModelList(videoList, hasNextPage, cursor)

    def getChannelClips(self, channel, filter, limit=100, cursor=""):
        variables = {
            "login": channel,
            "filter": filter,
            "limit": limit,
            "cursor": cursor
        }
        response = self.gql.api(getChannelClips, variables)
        clips = response["data"]["user"]["clips"]
        edges = clips["edges"]
        clipList = []
        for data in edges:
            clipList.append(Clip(data["node"]))
        hasNextPage = clips["pageInfo"]["hasNextPage"]
        if hasNextPage:
            cursor = edges[-1]["cursor"]
        else:
            cursor = None
        return ModelList(clipList, hasNextPage, cursor)

    def getVideo(self, id):
        variables = {
            "id": id
        }
        response = self.gql.api(getVideo, variables)
        video = response["data"]["video"]
        return self.errorIfNone(video, Video)

    def getClip(self, slug):
        variables = {
            "slug": slug
        }
        response = self.gql.api(getClip, variables)
        clip = response["data"]["clip"]
        return self.errorIfNone(clip, Clip)

api = TwitchGqlAPI()