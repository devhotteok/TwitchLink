from Core.Ui import *
from Services.Messages import Messages
from Services import ContentManager
from Services.Account import TwitchAccount
from Services.Twitch.Gql import TwitchGqlModels
from Services.Twitch.Playback import TwitchPlaybackAccessTokens
from Download.Downloader.Engine import Engine
from Download import ScheduledDownloadPreset
from Download.ScheduledDownloadManager import ScheduledDownloadManager
from Ui.Components.Widgets.WidgetRemoveController import WidgetRemoveController
from Ui.Components.Utils.ResolutionNameGenerator import ResolutionNameGenerator


class ScheduledDownloadPreview(QtWidgets.QWidget, UiFile.scheduledDownloadPreview):
    resizedSignal = QtCore.pyqtSignal()

    def __init__(self, scheduledDownloadId, parent=None):
        super(ScheduledDownloadPreview, self).__init__(parent=parent)
        self.scheduledDownloadId = scheduledDownloadId
        self.scheduledDownload = ScheduledDownloadManager.get(self.scheduledDownloadId)
        self.scheduledDownload.enabledChanged.connect(self.showEnableState)
        self.scheduledDownload.channelDataUpdateStarted.connect(self.channelDataUpdateStarted)
        self.scheduledDownload.channelDataUpdateFinished.connect(self.channelDataUpdateFinished)
        self.scheduledDownload.channelDataUpdated.connect(self.showChannel)
        self.scheduledDownload.channelConnected.connect(self.onChannelConnect)
        self.scheduledDownload.status.updated.connect(self.statusUpdated)
        self.statusUpdated()
        self.showLoading()
        self.widgetRemoveController = WidgetRemoveController(parent=self)
        self.widgetRemoveController.performRemove.connect(self.removeScheduledDownload)
        self.setup()
        if self.scheduledDownload.isChannelConnected():
            self.onChannelConnect()

    def showEvent(self, event):
        self.resizedSignal.emit()
        super().showEvent(event)

    def setup(self):
        self.viewIcon = Utils.setSvgIcon(self.viewIcon, Icons.VIEWER_ICON)
        self.adsInfoButton.clicked.connect(self.showAdsInfo)
        self.openFolderButton.clicked.connect(self.openFolder)
        self.openFileButton.clicked.connect(self.openFile)
        self.alertIcon = Utils.setSvgIcon(self.alertIcon, Icons.ALERT_RED_ICON)
        self.errorInfo.clicked.connect(self.showErrorInfo)
        self.showEnableState()
        self.enableButton.clicked.connect(self.enableButtonClicked)
        self.refreshButton.clicked.connect(self.scheduledDownload.updateChannelData)
        if self.scheduledDownload.isUpdatingChannelData():
            self.channelDataUpdateStarted()
        else:
            self.channelDataUpdateFinished()
        self.settingsButton.clicked.connect(self.editScheduledDownload)
        self.deleteButton.clicked.connect(self.tryRemoveScheduledDownload)
        self.hideDownloadInfo()

    def showEnableState(self):
        self.previewArea.setEnabled(self.scheduledDownload.isGloballyEnabled())
        self.enableButton.setIcon(QtGui.QIcon(Icons.TOGGLE_ON_ICON if self.scheduledDownload.isEnabled() else Icons.TOGGLE_OFF_ICON))

    def enableButtonClicked(self):
        if self.scheduledDownload.isEnabled():
            if self.scheduledDownload.status.isDownloading():
                if not self.ask(*Messages.ASK.STOP_DOWNLOAD):
                    return
        self.scheduledDownload.setEnabled(not self.scheduledDownload.isEnabled())

    def statusUpdated(self):
        if self.scheduledDownload.status.isNone():
            self.showStatus(False)
        elif self.scheduledDownload.status.isGeneratingAccessToken():
            self.showStatus(True, customMessage=T("preparing", ellipsis=True))
        elif self.scheduledDownload.status.isDownloading():
            self.connectDownloader(self.scheduledDownload.downloader)
            self.showStatus(True)
        elif self.scheduledDownload.status.isError():
            self.showStatus(True, error=self.scheduledDownload.status.getError())
        elif self.scheduledDownload.status.isDownloaderError():
            self.showStatus(True, error=self.scheduledDownload.status.getError(), isDownloadAborted=True)
        self.resizedSignal.emit()

    def showStatus(self, show, error=None, isDownloadAborted=False, customMessage=None):
        self._hideError()
        if show:
            self.statusArea.show()
            self.progressBar.setVisible(customMessage == None)
            if error != None:
                self._showError(error, isDownloadAborted=isDownloadAborted)
            elif customMessage != None:
                self.status.setText(customMessage)
                self.alertIcon.show()
                self.progressBar.hide()
        else:
            self.statusArea.hide()

    def connectDownloader(self, downloader):
        downloader.statusUpdate.connect(self.handleDownloadStatus)
        downloader.progressUpdate.connect(self.handleDownloadProgress)
        downloader.finished.connect(self.handleDownloadResult)
        self.showDownloadInfo(downloader.setup.downloadInfo)
        self.handleDownloadStatus(downloader.status)
        self.handleDownloadProgress(downloader.progress)
        self.widgetRemoveController.setRemoveEnabled(False)

    def disconnectDownloader(self, downloader):
        downloader.statusUpdate.disconnect(self.handleDownloadStatus)
        downloader.progressUpdate.disconnect(self.handleDownloadProgress)
        downloader.finished.disconnect(self.handleDownloadResult)
        self.hideDownloadInfo()
        self.widgetRemoveController.setRemoveEnabled(True)

    def handleDownloadStatus(self, status):
        if status.terminateState.isProcessing():
            self.enableButton.setEnabled(False)
            self.refreshButton.setEnabled(False)
            self.status.setText(T("stopping", ellipsis=True))
        elif status.isPreparing():
            self.status.setText(T("preparing", ellipsis=True))
        else:
            self.status.setText(T("live-downloading", ellipsis=True))

    def handleDownloadProgress(self, progress):
        self.duration.setText(Utils.formatTime(*Utils.toTime(progress.seconds)))
        self.currentSize.setText(progress.size)

    def handleDownloadResult(self, downloader):
        if downloader.status.terminateState.isTrue():
            self.enableButton.setEnabled(True)
            self.refreshButton.setEnabled(True)
        self.disconnectDownloader(downloader)

    def _showError(self, exception, isDownloadAborted=False):
        self.currentError = exception
        if isinstance(exception, Exceptions.FileSystemError):
            reasonText = "system-error"
        elif isinstance(exception, Exceptions.NetworkError):
            reasonText = "network-error"
        elif isinstance(exception, ContentManager.Exceptions.RestrictedContent):
            reasonText = "restricted-content"
        elif isinstance(exception, ScheduledDownloadPreset.Exceptions.PreferredResolutionNotFound):
            reasonText = "preferred-resolution-not-found"
        elif isinstance(exception, Engine.Exceptions.DownloaderCreationDisabled):
            reasonText = "disabled-feature"
        else:
            reasonText = "unknown-error"
        self.status.setText(f"{T('download-aborted')} ({T(reasonText)})" if isDownloadAborted else T(reasonText))
        self.alertIcon.show()
        self.errorInfo.show()
        self.progressBar.showError()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(100)

    def _hideError(self):
        self.alertIcon.hide()
        self.errorInfo.hide()
        self.progressBar.clearState()
        self.progressBar.setRange(0, 0)

    def showErrorInfo(self):
        if isinstance(self.currentError, TwitchPlaybackAccessTokens.Exceptions.Forbidden):
            if DB.account.isUserLoggedIn():
                self.info("unable-to-download", f"{T('#Authentication of your account has been denied.')}\n\n{T('reason')}: {self.currentError.reason}", contentTranslate=False)
            else:
                self.info("unable-to-download", f"{T('#Authentication denied.')}\n\n{T('reason')}: {self.currentError.reason}", contentTranslate=False)
        elif isinstance(self.currentError, TwitchPlaybackAccessTokens.Exceptions.GeoBlock):
            self.info("unable-to-download", f"{T('#This content is not available in your region.')}\n\n{T('reason')}: {self.currentError.reason}", contentTranslate=False)
        elif isinstance(self.currentError, TwitchPlaybackAccessTokens.Exceptions.ChannelNotFound):
            self.info("unable-to-download", "#Channel not found. Deleted or temporary error.")
        elif isinstance(self.currentError, ScheduledDownloadPreset.Exceptions.PreferredResolutionNotFound):
            self.info("unable-to-download", "#The preferred resolution was not found.\nYou have disabled the download until a matching resolution is found.")
        elif isinstance(self.currentError, Engine.Exceptions.DownloaderCreationDisabled):
            self.info("unable-to-download", "#Unable to start a new download.\nThis feature has been disabled.")
        else:
            self.handleExceptions(self.currentError)

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

    def channelDataUpdateStarted(self):
        self.refreshButton.setEnabled(False)
        if not self.scheduledDownload.isChannelConnected():
            self.showNetworkStatus(T("loading-channel-data", ellipsis=True))

    def channelDataUpdateFinished(self):
        self.refreshButton.setEnabled(True)
        if not self.scheduledDownload.isChannelConnected():
            self.showNetworkStatus(T("channel-not-found"))

    def editScheduledDownload(self):
        Ui.ScheduledDownloadSettings(self.scheduledDownload.preset, parent=self).exec()

    def onChannelConnect(self):
        self.showChannel()
        self.scheduledDownload.pubSubSubscriber.stateChanged.connect(self.showPubSubState)
        self.showPubSubState()

    def showLoading(self):
        self.channel.setText(self.scheduledDownload.preset.channel)
        self.showBroadcast(TwitchGqlModels.Channel({}))

    def showChannel(self):
        channel = self.scheduledDownload.channel
        self.channel.setText(channel.displayName)
        if channel.stream == None:
            self.showBroadcast(channel)
        else:
            self.showStream(channel.stream)

    def showBroadcast(self, channel):
        self.videoTypeLabel.setText(T("offline"))
        self.viewerCountArea.hide()
        self.thumbnailImage.loadImage(filePath=Images.OFFLINE_IMAGE, url=channel.offlineImageURL, urlFormatSize=ImageSize.CHANNEL_OFFLINE, refresh=True, clearImage=False)
        self.title.setText(channel.lastBroadcast.title)
        self.date.setText(channel.lastBroadcast.startedAt.toTimeZone(DB.localization.getTimezone()))
        self.categoryImage.loadImage(filePath=Images.CATEGORY_IMAGE, url=channel.lastBroadcast.game.boxArtURL, urlFormatSize=ImageSize.CATEGORY, clearImage=False)
        self.category.setText(channel.lastBroadcast.game.displayName)

    def showStream(self, stream):
        self.videoTypeLabel.setText(T("stream" if stream.isLive() else "rerun"))
        self.viewerCount.setText(stream.viewersCount)
        self.viewerCountArea.show()
        self.thumbnailImage.loadImage(filePath=Images.PREVIEW_IMAGE, url=stream.previewImageURL, urlFormatSize=ImageSize.STREAM_PREVIEW, refresh=True, clearImage=False)
        self.title.setText(stream.title)
        self.date.setText(stream.createdAt.toTimeZone(DB.localization.getTimezone()))
        self.categoryImage.loadImage(filePath=Images.CATEGORY_IMAGE, url=stream.game.boxArtURL, urlFormatSize=ImageSize.CATEGORY, clearImage=False)
        self.category.setText(stream.game.displayName)

    def showDownloadInfo(self, downloadInfo):
        if not downloadInfo.accessToken.hideAds:
            self.adsInfoButton.show()
        self.openFileButton.setEnabled(True)
        self.durationInfo.show()
        self.duration.show()
        self.resolutionInfo.show()
        self.resolution.show()
        self.fileInfo.show()
        self.file.show()
        self.currentSize.show()
        self.resolution.setText(ResolutionNameGenerator.generateResolutionName(downloadInfo.resolution))
        self.file.setText(downloadInfo.getAbsoluteFileName())

    def hideDownloadInfo(self):
        self.adsInfoButton.hide()
        self.openFileButton.setEnabled(False)
        self.durationInfo.hide()
        self.duration.hide()
        self.resolutionInfo.hide()
        self.resolution.hide()
        self.fileInfo.hide()
        self.file.hide()
        self.currentSize.hide()

    def showPubSubState(self):
        if self.scheduledDownload.pubSubSubscriber.isSubscribed():
            self.clearNetworkStatus()
        elif self.scheduledDownload.pubSubSubscriber.hasPendingRequest():
            self.showNetworkStatus(T("connecting", ellipsis=True))
        else:
            self.showNetworkStatus(T("not-connected"))

    def showNetworkStatus(self, text):
        self.networkStatusArea.show()
        self.networkStatus.setText(text)
        self.resizedSignal.emit()

    def clearNetworkStatus(self):
        self.networkStatusArea.hide()
        self.resizedSignal.emit()

    def showAdsInfo(self):
        self.info("warning", "#This stream may contain ads.\nTo block ads, you must log in with a subscribed account.\nChanges will take effect from the next download.")

    def openFolder(self):
        try:
            Utils.openFolder(self.scheduledDownload.preset.directory)
        except:
            self.info(*Messages.INFO.FOLDER_NOT_FOUND)

    def openFile(self):
        try:
            Utils.openFolder(self.scheduledDownload.downloader.setup.downloadInfo.getAbsoluteFileName())
        except:
            self.info(*Messages.INFO.FOLDER_NOT_FOUND)

    def tryRemoveScheduledDownload(self):
        if self.scheduledDownload.isEnabled():
            if self.scheduledDownload.status.isDownloading():
                if not self.ask(*Messages.ASK.STOP_DOWNLOAD):
                    return
            self.scheduledDownload.setEnabled(False)
        self.widgetRemoveController.registerRemove()

    def removeScheduledDownload(self):
        ScheduledDownloadManager.remove(self.scheduledDownloadId)