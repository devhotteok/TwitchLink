from Core.Ui import *
from Search import Engine
from Services.Messages import Messages
from Services.ContentManager import ContentManager
from Services.Twitch.Gql import TwitchGqlModels
from Services.Twitch.Playback import TwitchPlaybackAccessTokens
from Download.DownloadInfo import DownloadInfo
from Download.DownloadManager import DownloadManager


class VideoDownloadWidget(QtWidgets.QWidget, UiFile.videoDownloadWidget):
    accountPageShowRequested = QtCore.pyqtSignal()

    def __init__(self, data, resizable=True, parent=None):
        super(VideoDownloadWidget, self).__init__(parent=parent)
        self.data = data
        self.videoType = type(self.data)
        self.videoWidget = Utils.setPlaceholder(self.videoWidget, Ui.VideoWidget(self.data, resizable=resizable, parent=self))
        if self.videoType == TwitchGqlModels.Channel:
            self.downloadButton.setEnabled(False)
        elif self.videoType == TwitchGqlModels.Stream:
            self.downloadButton.clicked.connect(self.downloadStream)
        elif self.videoType == TwitchGqlModels.Video:
            self.downloadButton.clicked.connect(self.downloadVideo)
        elif self.videoType == TwitchGqlModels.Clip:
            self.downloadButton.clicked.connect(self.downloadClip)
        self.downloadButton.setText(T("live-download" if self.videoType == TwitchGqlModels.Channel or self.videoType == TwitchGqlModels.Stream else "download"))
        self.accessTokenThread = None

    def getAccessTokenThread(self):
        return self.accessTokenThread or Utils.WorkerThread(parent=self)

    def downloadStream(self):
        if self.isRestricted(self.data.broadcaster, self.data):
            return
        self.downloadButton.setEnabled(False)
        self.downloadButton.setText(T("loading", ellipsis=True))
        thread = self.getAccessTokenThread()
        thread.setup(
            target=Engine.Search.StreamAccessToken,
            args=(self.data.broadcaster.login, self.getAuthToken()),
            disconnect=True
        )
        thread.resultSignal.connect(self.processStreamAccessToken)
        thread.start()

    def processStreamAccessToken(self, result):
        self.downloadButton.setEnabled(True)
        self.downloadButton.setText(T("live-download"))
        if result.success:
            stream = result.data
            if stream.hideAds == False:
                if DB.account.isUserLoggedIn():
                    adBlockFailReason = "#Your account does not have a subscription to this channel."
                else:
                    adBlockFailReason = "#You are not currently logged in."
                if not self.ask("warning", T("#This stream contains ads.\n{appName} will block ads, but may fail, in which case an alternate screen will be displayed.\n\nTo completely block ads, you must log in with a subscribed account.\n{adBlockFailReason}\n\nProceed?", adBlockFailReason=T(adBlockFailReason), appName=Config.APP_NAME), contentTranslate=False):
                    return
            self.askDownload(DownloadInfo(self.data, stream))
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.Forbidden):
            if DB.account.isUserLoggedIn():
                self.info("unable-to-download", f"{T('#Authentication of your account has been denied.')}\n\n{T('reason')}: {result.error.reason}")
            else:
                self.info("unable-to-download", f"{T('#Authentication denied.')}\n\n{T('reason')}: {result.error.reason}")
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.GeoBlock):
            self.info("unable-to-download", f"{T('#This content is not available in your region.')}\n\n{T('reason')}: {result.error.reason}")
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.ChannelNotFound):
            self.info("unable-to-download", "#Channel not found. Deleted or temporary error.")
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.ChannelIsOffline):
            self.info("unable-to-download", "#Stream not found. Stream ended or temporary error.")
        else:
            self.handleExceptions(result.error)

    def downloadVideo(self):
        if self.isRestricted(self.data.owner, self.data):
            return
        self.downloadButton.setEnabled(False)
        self.downloadButton.setText(T("loading", ellipsis=True))
        thread = self.getAccessTokenThread()
        thread.setup(
            target=Engine.Search.VideoAccessToken,
            args=(self.data.id, self.getAuthToken()),
            disconnect=True
        )
        thread.resultSignal.connect(self.processVideoAccessToken)
        thread.start()

    def processVideoAccessToken(self, result):
        self.downloadButton.setEnabled(True)
        self.downloadButton.setText(T("download"))
        if result.success:
            video = result.data
            self.askDownload(DownloadInfo(self.data, video))
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.VideoRestricted):
            if DB.account.isUserLoggedIn():
                advice = T("#Unable to find subscription in your account.\nSubscribe to this streamer or log in with another account.")
                okText = "change-account"
            else:
                advice = T("#You need to log in to download subscriber-only videos.")
                okText = "login"
            if self.ask("unable-to-download", T("#This video is for subscribers only.\n{advice}", advice=advice), contentTranslate=False, okText=okText, cancelText="ok"):
                self.accountPageShowRequested.emit()
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.VideoNotFound):
            self.info("unable-to-download", "#Video not found. Deleted or temporary error.")
        else:
            self.handleExceptions(result.error)

    def downloadClip(self):
        if self.isRestricted(self.data.broadcaster, self.data):
            return
        self.downloadButton.setEnabled(False)
        self.downloadButton.setText(T("loading", ellipsis=True))
        thread = self.getAccessTokenThread()
        thread.setup(
            target=Engine.Search.ClipAccessToken,
            args=(self.data.slug, self.getAuthToken()),
            disconnect=True
        )
        thread.resultSignal.connect(self.processClipAccessToken)
        thread.start()

    def processClipAccessToken(self, result):
        self.downloadButton.setEnabled(True)
        self.downloadButton.setText(T("download"))
        if result.success:
            clip = result.data
            self.askDownload(DownloadInfo(self.data, clip))
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.ClipNotFound):
            self.info("unable-to-download", "#Clip not found. Deleted or temporary error.")
        else:
            self.handleExceptions(result.error)

    def isRestricted(self, channel, content):
        restriction = ContentManager.getRestrictions(channel, content)
        if restriction == None:
            return False
        else:
            self.info("content-restricted", restriction.message, contentTranslate=False)
            return True

    def getAuthToken(self):
        try:
            DB.account.checkAuthToken()
        except:
            self.info(*Messages.INFO.LOGIN_EXPIRED)
        return DB.account.getAuthToken()

    def handleExceptions(self, exception):
        if isinstance(exception, TwitchPlaybackAccessTokens.Exceptions.TokenError):
            if DB.account.isUserLoggedIn():
                self.info(*Messages.INFO.AUTHENTICATION_ERROR)
            else:
                self.info(*Messages.INFO.TEMPORARY_ERROR)
        else:
            self.info(*Messages.INFO.NETWORK_ERROR)

    def askDownload(self, downloadInfo):
        downloadInfo = Ui.DownloadMenu(downloadInfo, parent=self).exec()
        if downloadInfo != False:
            self.startDownload(downloadInfo)

    def startDownload(self, downloadInfo):
        DownloadManager.create(downloadInfo)