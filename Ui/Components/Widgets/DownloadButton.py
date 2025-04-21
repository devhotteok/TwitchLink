from Core.Ui import *
from Services.Messages import Messages
from Services import ContentManager
from Services.Twitch.GQL import TwitchGQLAPI
from Services.Twitch.GQL import TwitchGQLModels
from Services.Twitch.Playback import TwitchPlaybackGenerator
from Services.Twitch.Playback import TwitchPlaybackModels
from Download.DownloadInfo import DownloadInfo


class DownloadButton(QtCore.QObject):
    accountPageShowRequested = QtCore.pyqtSignal()

    def __init__(self, content: TwitchGQLModels.Channel | TwitchGQLModels.Stream | TwitchGQLModels.Video | TwitchGQLModels.Clip, button: QtWidgets.QPushButton | QtWidgets.QToolButton, buttonIcon: ThemedIcon | None = None, buttonText: str | None = None, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.button = button
        self.buttonText = buttonText
        self.content = content
        self.showLoading(False)
        if buttonIcon != None:
            Utils.setIconViewer(self.button, buttonIcon)
        if isinstance(content, TwitchGQLModels.Channel):
            self.button.setEnabled(False)
        elif isinstance(content, TwitchGQLModels.Stream):
            self.button.clicked.connect(self.downloadStream)
        elif isinstance(content, TwitchGQLModels.Video):
            self.button.clicked.connect(self.downloadVideo)
        elif isinstance(content, TwitchGQLModels.Clip):
            self.button.clicked.connect(self.downloadClip)

    def info(self, title: str, content: str, titleTranslate: bool = True, contentTranslate: bool = True, buttonText: str | None = None) -> None:
        Utils.info(title, content, titleTranslate, contentTranslate, buttonText, parent=self.button)

    def ask(self, title: str, content: str, titleTranslate: bool = True, contentTranslate: bool = True, okText: str | None = None, cancelText: str | None = None, defaultOk: bool = False) -> bool:
        return Utils.ask(title, content, titleTranslate, contentTranslate, okText, cancelText, defaultOk, parent=self.button)

    def showLoading(self, loading: bool) -> None:
        self.button.setEnabled(not loading)
        if self.buttonText != None:
            self.button.setText(T("loading", ellipsis=True) if loading else self.buttonText)

    def downloadStream(self) -> None:
        try:
            App.ContentManager.checkRestriction(self.content)
        except Exception as e:
            self.handleExceptions(e)
        else:
            self.showLoading(True)
            TwitchPlaybackGenerator.TwitchStreamPlaybackGenerator(self.content.broadcaster.login, parent=self).finished.connect(self._processStreamPlaybackResult)

    def _processStreamPlaybackResult(self, generator: TwitchPlaybackGenerator.TwitchStreamPlaybackGenerator) -> None:
        self.showLoading(False)
        if generator.getError() == None:
            streamPlayback = generator.getData()
            if not streamPlayback.token.hideAds:
                if not self.showStreamAdWarning():
                    return
            self.askDownload(self.generateDownloadInfo(streamPlayback))
        elif isinstance(generator.getError(), TwitchPlaybackGenerator.Exceptions.Forbidden):
            if App.Account.isLoggedIn():
                self.info("unable-to-download", f"{T('#Authentication of your account has been denied.')}\n\n{T('reason')}: {generator.getError().reason}", contentTranslate=False)
            else:
                self.info("unable-to-download", f"{T('#Authentication denied.')}\n\n{T('reason')}: {generator.getError().reason}", contentTranslate=False)
        elif isinstance(generator.getError(), TwitchPlaybackGenerator.Exceptions.GeoBlock):
            self.info("unable-to-download", f"{T('#This content is not available in your region.')}\n\n{T('reason')}: {generator.getError().reason}", contentTranslate=False)
        elif isinstance(generator.getError(), TwitchPlaybackGenerator.Exceptions.ChannelNotFound):
            self.info("unable-to-download", "#Channel not found. Deleted or temporary error.")
        elif isinstance(generator.getError(), TwitchPlaybackGenerator.Exceptions.ChannelIsOffline):
            self.info("unable-to-download", "#Stream not found. Stream ended or temporary error.")
        else:
            self.handleExceptions(generator.getError())

    def downloadVideo(self) -> None:
        try:
            App.ContentManager.checkRestriction(self.content)
        except Exception as e:
            self.handleExceptions(e)
        else:
            self.showLoading(True)
            TwitchPlaybackGenerator.TwitchVideoPlaybackGenerator(self.content.id, parent=self).finished.connect(self._processVideoPlaybackResult)

    def _processVideoPlaybackResult(self, generator: TwitchPlaybackGenerator.TwitchStreamPlaybackGenerator) -> None:
        self.showLoading(False)
        if generator.getError() == None:
            videoPlayback = generator.getData()
            self.askDownload(self.generateDownloadInfo(videoPlayback))
        elif isinstance(generator.getError(), TwitchPlaybackGenerator.Exceptions.VideoRestricted):
            if App.Account.isLoggedIn():
                advice = T("#Unable to find subscription in your account.\nSubscribe to this streamer or log in with another account.")
                okText = T("change-account")
            else:
                advice = T("#You need to log in to download subscriber-only videos.")
                okText = T("log-in")
            if self.ask("unable-to-download", T("#This video is for subscribers only.\n{advice}", advice=advice), contentTranslate=False, okText=okText, cancelText=T("ok")):
                self.accountPageShowRequested.emit()
        elif isinstance(generator.getError(), TwitchPlaybackGenerator.Exceptions.VideoNotFound):
            self.info("unable-to-download", "#Video not found. Deleted or temporary error.")
        else:
            self.handleExceptions(generator.getError())

    def downloadClip(self) -> None:
        try:
            App.ContentManager.checkRestriction(self.content)
        except Exception as e:
            self.handleExceptions(e)
        else:
            self.showLoading(True)
            TwitchPlaybackGenerator.TwitchClipPlaybackGenerator(self.content.slug, parent=self).finished.connect(self._processClipPlaybackResult)

    def _processClipPlaybackResult(self, generator: TwitchPlaybackGenerator.TwitchStreamPlaybackGenerator) -> None:
        self.showLoading(False)
        if generator.getError() == None:
            clipPlayback = generator.getData()
            self.askDownload(self.generateDownloadInfo(clipPlayback))
        elif isinstance(generator.getError(), TwitchPlaybackGenerator.Exceptions.ClipNotFound):
            self.info("unable-to-download", "#Clip not found. Deleted or temporary error.")
        else:
            self.handleExceptions(generator.getError())

    def handleExceptions(self, exception: Exception) -> None:
        if isinstance(exception, TwitchGQLAPI.Exceptions.AuthorizationError):
            if App.Account.isLoggedIn():
                self.info(*Messages.INFO.AUTHENTICATION_ERROR)
            else:
                self.info(*Messages.INFO.TEMPORARY_ERROR)
        elif isinstance(exception, ContentManager.Exceptions.RestrictedContent):
            self.handleRestrictedContent(exception)
        else:
            self.info(*Messages.INFO.NETWORK_ERROR)

    def handleRestrictedContent(self, restriction: ContentManager.Exceptions.RestrictedContent) -> None:
        if restriction.restrictionType == ContentManager.RestrictionType.CONTENT_TYPE:
            restrictionType = T("#Downloading {contentType} from this channel has been restricted by the streamer({channel})'s request or by the administrator.", channel=restriction.channel.displayName, contentType=T(restriction.contentType))
        else:
            restrictionType = T("#This content has been restricted by the streamer({channel})'s request or by the administrator.", channel=restriction.channel.displayName)
        restrictionInfo = T("#To protect the rights of streamers, {appName} restricts downloads when a content restriction request is received.", appName=Config.APP_NAME)
        message = f"{restrictionType}\n\n{restrictionInfo}"
        if restriction.reason != None:
            message = f"{message}\n\n[{T('reason')}]\n{restriction.reason}"
        self.info("restricted-content", message, contentTranslate=False)

    def generateDownloadInfo(self, playback: TwitchPlaybackModels.TwitchStreamPlayback | TwitchPlaybackModels.TwitchVideoPlayback | TwitchPlaybackModels.TwitchClipPlayback) -> DownloadInfo:
        return DownloadInfo(self.content, playback)

    def showStreamAdWarning(self) -> bool:
        adsInfo = T("#This stream may contain ads.\nIf commercials are broadcast, the portion of the stream during the commercials may not be available for download, and it may appear as though the stream is interrupted.\nTo prevent ads, you need to log in with an account that has ad-free benefits, such as Twitch Turbo, or an account that subscribes to the channel.")
        if App.Account.isLoggedIn():
            adBlockFailReason = T("#Your account does not have a subscription to this channel.")
        else:
            adBlockFailReason = T("#You are not currently logged in.")
        proceedInfo = T("#Would you like to proceed?")
        return self.ask("warning", f"{adsInfo}\n\n{adBlockFailReason}\n\n{proceedInfo}", contentTranslate=False, defaultOk=True)

    def askDownload(self, downloadInfo: DownloadInfo) -> None:
        downloadMenu = Ui.DownloadMenu(downloadInfo, parent=self.button)
        downloadMenu.downloadRequested.connect(self.startDownload, QtCore.Qt.ConnectionType.QueuedConnection)
        downloadMenu.exec()

    def startDownload(self, downloadInfo: DownloadInfo) -> None:
        try:
            App.DownloadManager.create(downloadInfo)
        except ContentManager.Exceptions.RestrictedContent as e:
            self.handleRestrictedContent(e)
        except:
            self.info(*Messages.INFO.ACTION_PERFORM_ERROR)