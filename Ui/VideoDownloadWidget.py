from Core.App import App
from Core.Ui import *
from Search import Engine
from Services.Messages import Messages
from Services.ContentManager import ContentManager
from Services.Twitch.Gql import TwitchGqlModels
from Services.Twitch.Playback import TwitchPlaybackAccessTokens
from Download.DownloadInfo import DownloadInfo


class VideoDownloadWidget(QtWidgets.QWidget, UiFile.videoDownloadWidget):
    def __init__(self, window, data, resizable=True):
        super().__init__()
        self.window = window
        self.data = data
        self.videoType = type(self.data)
        if resizable == False:
            self.setContentsMargins(10, 10, 10, 10)
        Utils.setPlaceholder(self.videoWidgetPlaceholder, Ui.VideoWidget(self.data, resizable=resizable))
        if self.videoType == TwitchGqlModels.Channel:
            self.downloadButton.setEnabled(False)
        elif self.videoType == TwitchGqlModels.Stream:
            self.downloadButton.clicked.connect(self.downloadStream)
        elif self.videoType == TwitchGqlModels.Video:
            self.downloadButton.clicked.connect(self.downloadVideo)
        elif self.videoType == TwitchGqlModels.Clip:
            self.downloadButton.clicked.connect(self.downloadClip)
        self.downloadButton.setText(T("live-download" if self.videoType == TwitchGqlModels.Channel or self.videoType == TwitchGqlModels.Stream else "download"))

    def downloadStream(self):
        if self.isRestricted(self.data.broadcaster, self.data):
            return
        self.window.setLoading(True)
        self.window.setDownloadEnabled(False)
        self.downloadButton.setText(T("loading", ellipsis=True))
        self.streamAccessTokenThread = Engine.SearchThread(
            target=Engine.Search.StreamAccessToken,
            callback=self.processStreamAccessToken,
            args=(self.data.broadcaster.login, self.getAuthToken())
        )

    def processStreamAccessToken(self, result):
        self.window.setLoading(False)
        self.window.setDownloadEnabled(True)
        self.downloadButton.setText(T("live-download"))
        if result.success:
            stream = result.data
            if stream.found != True:
                if stream.found == TwitchPlaybackAccessTokens.Exceptions.ChannelNotFound:
                    Utils.info("unable-to-download", "#Channel not found. Deleted or temporary error.")
                elif stream.found == TwitchPlaybackAccessTokens.Exceptions.ChannelIsOffline:
                    Utils.info("unable-to-download", "#Stream not found. Stream ended or temporary error.")
                else:
                    Utils.info(*Messages.INFO.NETWORK_ERROR)
                return
            if stream.hideAds == False:
                if DB.account.isUserLoggedIn():
                    if not Utils.ask("warning", "#Twitch's ads can't be blocked during the stream because your account doesn't have any subscription to this channel.\nProceed?", defaultOk=True):
                        return
                else:
                    if not Utils.ask("warning", "#To block Twitch ads during the stream, you need to log in with your subscribed account.\nYou are currently not logged in and cannot block Twitch ads during the stream.\nProceed?", defaultOk=True):
                        return
            self.window.downloadStream(DownloadInfo(self.data, stream))
        else:
            self.handleExceptions(result.error)

    def downloadVideo(self):
        if self.isRestricted(self.data.owner, self.data):
            return
        self.window.setLoading(True)
        self.window.setDownloadEnabled(False)
        self.downloadButton.setText(T("loading", ellipsis=True))
        self.videoAccessTokenThread = Engine.SearchThread(
            target=Engine.Search.VideoAccessToken,
            callback=self.processVideoAccessToken,
            args=(self.data.id, self.getAuthToken())
        )

    def processVideoAccessToken(self, result):
        self.window.setLoading(False)
        self.window.setDownloadEnabled(True)
        self.downloadButton.setText(T("download"))
        if result.success:
            video = result.data
            if video.found != True:
                if video.found == TwitchPlaybackAccessTokens.Exceptions.VideoRestricted:
                    if DB.account.isUserLoggedIn():
                        advice = T("#Unable to find subscription in your account.\nSubscribe to this streamer or log in with another account.")
                        okText = "change-account"
                    else:
                        advice = T("#You need to log in to download subscriber-only videos.")
                        okText = "login"
                    if Utils.ask("unable-to-download", "#This video is for subscribers only.\n{advice}", okText=okText, cancelText="ok", advice=advice):
                        App.coreWindow().openAccount()
                elif video.found == TwitchPlaybackAccessTokens.Exceptions.VideoNotFound:
                    Utils.info("unable-to-download", "#Video not found. Deleted or temporary error.")
                else:
                    Utils.info(*Messages.INFO.NETWORK_ERROR)
                return
            self.window.downloadVideo(DownloadInfo(self.data, video))
        else:
            self.handleExceptions(result.error)

    def downloadClip(self):
        if self.isRestricted(self.data.broadcaster, self.data):
            return
        self.window.setLoading(True)
        self.window.setDownloadEnabled(False)
        self.downloadButton.setText(T("loading", ellipsis=True))
        self.clipAccessTokenThread = Engine.SearchThread(
            target=Engine.Search.ClipAccessToken,
            callback=self.processClipAccessToken,
            args=(self.data.slug, self.getAuthToken())
        )

    def processClipAccessToken(self, result):
        self.window.setLoading(False)
        self.window.setDownloadEnabled(True)
        self.downloadButton.setText(T("download"))
        if result.success:
            clip = result.data
            if clip.found != True:
                if clip.found == TwitchPlaybackAccessTokens.Exceptions.ClipNotFound:
                    Utils.info("unable-to-download", "#Clip not found. Deleted or temporary error.")
                else:
                    Utils.info(*Messages.INFO.NETWORK_ERROR)
                return
            self.window.downloadClip(DownloadInfo(self.data, clip))
        else:
            self.handleExceptions(result.error)

    def isRestricted(self, channel, content):
        restriction = ContentManager.getRestrictions(channel, content)
        if restriction == None:
            return False
        else:
            Utils.info("content-restricted", restriction.message)
            return True

    def getAuthToken(self):
        try:
            DB.account.checkAuthToken()
        except:
            Utils.info(*Messages.INFO.LOGIN_EXPIRED)
        return DB.account.getAuthToken()

    def handleExceptions(self, exception):
        if exception == TwitchPlaybackAccessTokens.Exceptions.TokenError:
            if DB.account.isUserLoggedIn():
                Utils.info(*Messages.INFO.AUTHENTICATION_ERROR)
            else:
                Utils.info(*Messages.INFO.TEMPORARY_ERROR)
        else:
            Utils.info(*Messages.INFO.NETWORK_ERROR)