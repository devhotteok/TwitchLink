from Core.Ui import *
from Services.ContentManager import ContentManager
from Search import Engine


class AccessTokenGenerator(QtCore.QObject):
    def __init__(self, videoData, parent=None):
        super(AccessTokenGenerator, self).__init__(parent=parent)
        self.videoData = videoData
        self.accessTokenThread = None

    def getAccessTokenThread(self):
        return self.accessTokenThread or Utils.WorkerThread(parent=self)

    def getAuthToken(self):
        DB.account.checkAuthToken()
        return DB.account.getAuthToken()

    def _generateAccessToken(self, process, resultHandler):
        thread = self.getAccessTokenThread()
        thread.setup(
            target=process,
            disconnect=True
        )
        thread.resultSignal.connect(resultHandler)
        thread.start()

    def generateStreamAccessToken(self):
        self._generateAccessToken(
            self.streamAccessTokenProcess,
            self.processStreamAccessTokenResult
        )

    def streamAccessTokenProcess(self):
        ContentManager.checkRestrictions(self.videoData, user=DB.account.user, fetch=True)
        return Engine.Search.StreamAccessToken(self.videoData.broadcaster.login, self.getAuthToken())

    def processStreamAccessTokenResult(self, result):
        pass

    def generateVideoAccessToken(self):
        self._generateAccessToken(
            self.videoAccessTokenProcess,
            self.processVideoAccessTokenResult
        )

    def videoAccessTokenProcess(self):
        ContentManager.checkRestrictions(self.videoData, user=DB.account.user, fetch=True)
        return Engine.Search.VideoAccessToken(self.videoData.id, self.getAuthToken())

    def processVideoAccessTokenResult(self, result):
        pass

    def generateClipAccessToken(self):
        self._generateAccessToken(
            self.clipAccessTokenProcess,
            self.processClipAccessTokenResult
        )

    def clipAccessTokenProcess(self):
        ContentManager.checkRestrictions(self.videoData, user=DB.account.user, fetch=True)
        return Engine.Search.ClipAccessToken(self.videoData.slug, self.getAuthToken())

    def processClipAccessTokenResult(self, result):
        pass