from Services.ContentManager import ContentManager
from Database.Database import DB
from Search import Engine


class AccessTokenGenerator:
    @classmethod
    def generateStreamAccessToken(cls, videoData):
        ContentManager.checkRestrictions(videoData, user=DB.account.user, fetch=True)
        return Engine.Search.StreamAccessToken(videoData.broadcaster.login, DB.account.getAuthToken())

    @classmethod
    def generateVideoAccessToken(cls, videoData):
        ContentManager.checkRestrictions(videoData, user=DB.account.user, fetch=True)
        return Engine.Search.VideoAccessToken(videoData.id, DB.account.getAuthToken())

    @classmethod
    def generateClipAccessToken(cls, videoData):
        ContentManager.checkRestrictions(videoData, user=DB.account.user, fetch=True)
        return Engine.Search.ClipAccessToken(videoData.slug, DB.account.getAuthToken())