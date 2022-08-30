from Core.Ui import *
from Services import ContentManager
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

    def generateStreamAccessToken(self):
        thread = self.getAccessTokenThread()
        thread.setup(
            target=self.streamAccessTokenProcess,
            disconnect=True
        )
        thread.resultSignal.connect(self.processStreamAccessTokenResult)
        thread.start()

    def streamAccessTokenProcess(self):
        ContentManager.ContentManager.checkRestrictions(self.videoData.broadcaster, self.videoData)
        return Engine.Search.StreamAccessToken(self.videoData.broadcaster.login, self.getAuthToken())

    def processStreamAccessTokenResult(self, result):
        pass

    def generateVideoAccessToken(self):
        thread = self.getAccessTokenThread()
        thread.setup(
            target=self.videoAccessTokenProcess,
            disconnect=True
        )
        thread.resultSignal.connect(self.processVideoAccessTokenResult)
        thread.start()

    def videoAccessTokenProcess(self):
        ContentManager.ContentManager.checkRestrictions(self.videoData.owner, self.videoData)
        return Engine.Search.VideoAccessToken(self.videoData.id, self.getAuthToken())

    def processVideoAccessTokenResult(self, result):
        pass

    def generateClipAccessToken(self):
        thread = self.getAccessTokenThread()
        thread.setup(
            target=self.clipAccessTokenProcess,
            disconnect=True
        )
        thread.resultSignal.connect(self.processClipAccessTokenResult)
        thread.start()

    def clipAccessTokenProcess(self):
        ContentManager.ContentManager.checkRestrictions(self.videoData.broadcaster, self.videoData)
        return Engine.Search.ClipAccessToken(self.videoData.slug, self.getAuthToken())

    def processClipAccessTokenResult(self, result):
        pass