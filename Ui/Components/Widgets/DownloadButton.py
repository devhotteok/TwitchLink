from Core.Ui import *
from Services.Messages import Messages
from Services import ContentManager
from Services.Account import TwitchAccount
from Services.Twitch.Gql import TwitchGqlModels
from Services.Twitch.Playback import TwitchPlaybackAccessTokens
from Services.AccessTokenGenerator import AccessTokenGenerator
from Download.DownloadInfo import DownloadInfo
from Download.DownloadManager import DownloadManager


class DownloadButton(QtCore.QObject):
    accountPageShowRequested = QtCore.pyqtSignal()

    def __init__(self, videoData, button, buttonText=None, parent=None):
        super(DownloadButton, self).__init__(parent=parent)
        self.button = button
        self.buttonText = buttonText
        self.videoData = videoData
        self.videoType = type(self.videoData)
        self.showLoading(False)
        if self.videoType == TwitchGqlModels.Channel:
            self.button.setEnabled(False)
        elif self.videoType == TwitchGqlModels.Stream:
            self.button.clicked.connect(self.downloadStream)
        elif self.videoType == TwitchGqlModels.Video:
            self.button.clicked.connect(self.downloadVideo)
        elif self.videoType == TwitchGqlModels.Clip:
            self.button.clicked.connect(self.downloadClip)
        self.accessTokenThread = None

    def getAccessTokenThread(self):
        if self.accessTokenThread == None:
            self.accessTokenThread = Utils.WorkerThread(parent=self)
        return self.accessTokenThread

    def generateAccessToken(self, process, resultHandler):
        thread = self.getAccessTokenThread()
        thread.setup(
            target=process,
            args=(self.videoData,),
            disconnect=True
        )
        thread.resultSignal.connect(resultHandler)
        thread.start()

    def info(self, title, content, titleTranslate=True, contentTranslate=True, buttonText=None):
        Utils.info(title, content, titleTranslate, contentTranslate, buttonText, parent=self.button)

    def ask(self, title, content, titleTranslate=True, contentTranslate=True, okText=None, cancelText=None, defaultOk=False):
        return Utils.ask(title, content, titleTranslate, contentTranslate, okText, cancelText, defaultOk, parent=self.button)

    def showLoading(self, loading):
        self.button.setEnabled(not loading)
        if self.buttonText != None:
            self.button.setText(T("loading", ellipsis=True) if loading else self.buttonText)

    def downloadStream(self):
        self.showLoading(True)
        self.generateAccessToken(
            AccessTokenGenerator.generateStreamAccessToken,
            self.processStreamAccessTokenResult
        )

    def processStreamAccessTokenResult(self, result):
        self.showLoading(False)
        if result.success:
            stream = result.data
            if stream.hideAds == False:
                if DB.account.isUserLoggedIn():
                    adBlockFailReason = "#Your account does not have a subscription to this channel."
                else:
                    adBlockFailReason = "#You are not currently logged in."
                if not self.ask("warning", T("#This stream may contain ads.\n{appName} will block ads, but may fail, in which case an alternate screen will be displayed.\n\nTo completely block ads, you must log in with a subscribed account.\n{adBlockFailReason}\n\nProceed?", adBlockFailReason=T(adBlockFailReason), appName=Config.APP_NAME), contentTranslate=False, defaultOk=True):
                    return
            self.askDownload(self.generateDownloadInfo(stream))
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.Forbidden):
            if DB.account.isUserLoggedIn():
                self.info("unable-to-download", f"{T('#Authentication of your account has been denied.')}\n\n{T('reason')}: {result.error.reason}", contentTranslate=False)
            else:
                self.info("unable-to-download", f"{T('#Authentication denied.')}\n\n{T('reason')}: {result.error.reason}", contentTranslate=False)
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.GeoBlock):
            self.info("unable-to-download", f"{T('#This content is not available in your region.')}\n\n{T('reason')}: {result.error.reason}", contentTranslate=False)
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.ChannelNotFound):
            self.info("unable-to-download", "#Channel not found. Deleted or temporary error.")
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.ChannelIsOffline):
            self.info("unable-to-download", "#Stream not found. Stream ended or temporary error.")
        else:
            self.handleExceptions(result.error)

    def downloadVideo(self):
        self.showLoading(True)
        self.generateAccessToken(
            AccessTokenGenerator.generateVideoAccessToken,
            self.processVideoAccessTokenResult
        )

    def processVideoAccessTokenResult(self, result):
        self.showLoading(False)
        if result.success:
            video = result.data
            self.askDownload(self.generateDownloadInfo(video))
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
        self.showLoading(True)
        self.generateAccessToken(
            AccessTokenGenerator.generateClipAccessToken,
            self.processClipAccessTokenResult
        )

    def processClipAccessTokenResult(self, result):
        self.showLoading(False)
        if result.success:
            clip = result.data
            self.askDownload(self.generateDownloadInfo(clip))
        elif isinstance(result.error, TwitchPlaybackAccessTokens.Exceptions.ClipNotFound):
            self.info("unable-to-download", "#Clip not found. Deleted or temporary error.")
        else:
            self.handleExceptions(result.error)

    def handleExceptions(self, exception):
        if isinstance(exception, TwitchAccount.Exceptions.InvalidToken):
            self.info(*Messages.INFO.LOGIN_EXPIRED)
        elif isinstance(exception, TwitchPlaybackAccessTokens.Exceptions.TokenError):
            if DB.account.isUserLoggedIn():
                self.info(*Messages.INFO.AUTHENTICATION_ERROR)
            else:
                self.info(*Messages.INFO.TEMPORARY_ERROR)
        elif isinstance(exception, ContentManager.Exceptions.RestrictedContent):
            self.handleRestrictedContent(exception)
        else:
            self.info(*Messages.INFO.NETWORK_ERROR)

    def handleRestrictedContent(self, restriction):
        if restriction.restrictionType == ContentManager.RestrictionType.CONTENT_TYPE:
            restrictionType = T("#Downloading {contentType} from this channel has been restricted by the streamer({channel})'s request or by the administrator.", channel=restriction.channel.displayName, contentType=T(restriction.contentType))
        else:
            restrictionType = T("#This content has been restricted by the streamer({channel})'s request or by the administrator.", channel=restriction.channel.displayName)
        restrictionInfo = T("#To protect the rights of streamers, {appName} restricts downloads when a content restriction request is received.", appName=Config.APP_NAME)
        message = f"{restrictionType}\n\n{restrictionInfo}"
        if restriction.reason != None:
            message = f"{message}\n\n[{T('reason')}]\n{restriction.reason}"
        self.info("restricted-content", message, contentTranslate=False)

    def generateDownloadInfo(self, accessToken):
        return DownloadInfo(self.videoData, accessToken)

    def askDownload(self, downloadInfo):
        downloadInfo = Ui.DownloadMenu(downloadInfo, parent=self.button).exec()
        if downloadInfo != False:
            self.startDownload(downloadInfo)

    def startDownload(self, downloadInfo):
        try:
            ContentManager.ContentManager.checkRestrictions(self.videoData, user=DB.account.user)
            DownloadManager.create(downloadInfo)
        except ContentManager.Exceptions.RestrictedContent as e:
            self.handleRestrictedContent(e)
        except:
            self.info(*Messages.INFO.ACTION_PERFORM_ERROR)