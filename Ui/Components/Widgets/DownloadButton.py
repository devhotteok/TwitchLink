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
            if App.Account.isSignedIn():
                self.info("unable-to-download", f"{T("errors.#authentication_your_account_has_been_de")}\n\n{T('reason')}: {generator.getError().reason}", contentTranslate=False)
            else:
                self.info("unable-to-download", f"{T("errors.#authentication_denied")}\n\n{T('reason')}: {generator.getError().reason}", contentTranslate=False)
        elif isinstance(generator.getError(), TwitchPlaybackGenerator.Exceptions.GeoBlock):
            self.info("unable-to-download", f"{T("info.#this_content_is_not_available_your_regi")}\n\n{T('reason')}: {generator.getError().reason}", contentTranslate=False)
        elif isinstance(generator.getError(), TwitchPlaybackGenerator.Exceptions.ChannelNotFound):
            self.info("unable-to-download", "errors.#channel_not_found_deleted_or_temporary")
        elif isinstance(generator.getError(), TwitchPlaybackGenerator.Exceptions.ChannelIsOffline):
            self.info("unable-to-download", "errors.#stream_not_found_stream_ended_or_tempor")
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
            if App.Account.isSignedIn():
                advice = T("errors.#unable_find_subscription_your_account_s")
                okText = T("change-account")
            else:
                advice = T("messages.#you_need_sign_download_subscriber_only")
                okText = T("sign-in")
            if self.ask("unable-to-download", T("messages.#this_video_is_subscribers_only", advice=advice), contentTranslate=False, okText=okText, cancelText=T("ok")):
                self.accountPageShowRequested.emit()
        elif isinstance(generator.getError(), TwitchPlaybackGenerator.Exceptions.VideoNotFound):
            self.info("unable-to-download", "errors.#video_not_found_deleted_or_temporary_er")
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
            self.info("unable-to-download", "errors.#clip_not_found_deleted_or_temporary_err")
        else:
            self.handleExceptions(generator.getError())

    def handleExceptions(self, exception: Exception) -> None:
        if isinstance(exception, TwitchGQLAPI.Exceptions.AuthorizationError):
            if App.Account.isSignedIn():
                self.info(*Messages.INFO.AUTHENTICATION_ERROR)
            else:
                self.info(*Messages.INFO.TEMPORARY_ERROR)
        elif isinstance(exception, ContentManager.Exceptions.RestrictedContent):
            self.handleRestrictedContent(exception)
        else:
            self.info(*Messages.INFO.NETWORK_ERROR)

    def handleRestrictedContent(self, restriction: ContentManager.Exceptions.RestrictedContent) -> None:
        if restriction.restrictionType == ContentManager.RestrictionType.CONTENT_TYPE:
            restrictionType = T("errors.#downloading_this_channel_has_been_restr", channel=restriction.channel.displayName, contentType=T(restriction.contentType))
        else:
            restrictionType = T("errors.#this_content_has_been_restricted_stream", channel=restriction.channel.displayName)
        restrictionInfo = T("messages.#to_protect_rights_streamers_restricts_d", appName=Config.APP_NAME)
        message = f"{restrictionType}\n\n{restrictionInfo}"
        if restriction.reason != None:
            message = f"{message}\n\n[{T('reason')}]\n{restriction.reason}"
        self.info("restricted-content", message, contentTranslate=False)

    def generateDownloadInfo(self, playback: TwitchPlaybackModels.TwitchStreamPlayback | TwitchPlaybackModels.TwitchVideoPlayback | TwitchPlaybackModels.TwitchClipPlayback) -> DownloadInfo:
        return DownloadInfo(self.content, playback)

    def showStreamAdWarning(self) -> bool:
        adsInfo = T("info.#this_stream_may_contain_ads_if_commerci")
        if App.Account.isSignedIn():
            adBlockFailReason = T("messages.#your_account_does_not_have_subscription")
        else:
            adBlockFailReason = T("messages.#you_are_not_currently_signed")
        proceedInfo = T("prompts.#would_you_like_proceed")
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