from Core.Ui import *
from Services.Messages import Messages
from Services.PartnerContent.PartnerContentInFeedWidgetListViewer import PartnerContentInFeedWidgetListViewer
from Services.Twitch.GQL import TwitchGQLAPI
from Services.Twitch.GQL import TwitchGQLModels


class SearchResult(QtWidgets.QWidget):
    accountPageShowRequested = QtCore.pyqtSignal()

    DEFAULT_CHANNEL_PRIMARY_COLOR = "9147ff"

    SEARCH_SCROLL_THRESHOLD = 300

    SEARCH_TYPES = [
        ("past-broadcasts", "ARCHIVE"),
        ("highlights", "HIGHLIGHT"),
        ("clips", None),
        ("uploads", "UPLOAD"),
        ("past-premiers", "PAST_PREMIERE"),
        ("all-videos", None)
    ]

    SORT_LIST = [
        ("date", "TIME"),
        ("popular", "VIEWS")
    ]

    FILTER_LIST = [
        ("24h", "LAST_DAY"),
        ("7d", "LAST_WEEK"),
        ("30d", "LAST_MONTH"),
        ("all", "ALL_TIME")
    ]

    def __init__(self, data: TwitchGQLModels.Channel | TwitchGQLModels.Video | TwitchGQLModels.Clip, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.data = data
        self._ui = UiLoader.load("searchResult", self)
        App.ThemeManager.themeUpdated.connect(self._setupThemeStyle)
        self._setupThemeStyle()
        self._ui.viewIcon = Utils.setSvgIcon(self._ui.viewIcon, Icons.VIEWER)
        self._ui.verifiedIcon = Utils.setSvgIcon(self._ui.verifiedIcon, Icons.VERIFIED)
        self._ui.infoIcon = Utils.setSvgIcon(self._ui.infoIcon, Icons.INFO)
        self._ui.loadingIcon = Utils.setSvgIcon(self._ui.loadingIcon, Icons.INFO)
        self._ui.videoArea.setStyleSheet("#videoArea {background-color: transparent;}")
        self._ui.videoArea.verticalScrollBar().valueChanged.connect(self.searchMoreVideos)
        self._widgetListViewer = PartnerContentInFeedWidgetListViewer(self._ui.videoArea, responsive=False, parent=self)
        self.setup()

    def _setupThemeStyle(self) -> None:
        self._ui.stackedWidget.setStyleSheet(f"#stackedWidget {{background-color: {App.Instance.palette().color(QtGui.QPalette.ColorGroup.Normal, QtGui.QPalette.ColorRole.Window).name()};}}")

    def setLoading(self, loading: bool, showErrorMessage: bool = False) -> None:
        self._loading = loading
        if self.isLoading():
            self._ui.searchType.setEnabled(False)
            self._ui.sortOrFilter.setEnabled(False)
            self._ui.refreshVideoListButton.setEnabled(False)
            self._ui.statusLabel.setText(T("loading", ellipsis=True))
            self._ui.loadingInfoArea.show()
        else:
            self._ui.searchType.setEnabled(True)
            self._ui.sortOrFilter.setEnabled(True)
            self._ui.refreshVideoListButton.setEnabled(True)
            self._ui.statusLabel.setText(T("#A temporary error has occurred.\nPlease try again later." if showErrorMessage else "no-results-found"))
            self._ui.loadingInfoArea.hide()
        if self._widgetListViewer.count() == 0:
            self._ui.stackedWidget.setCurrentIndex(0)
        else:
            self._ui.stackedWidget.setCurrentIndex(1)

    def isLoading(self) -> bool:
        return self._loading

    def setup(self) -> None:
        if type(self.data) == TwitchGQLModels.Channel:
            self.showChannel(self.data)
            self._ui.searchType.addItems([T(item[0]) for item in self.SEARCH_TYPES])
            self._ui.searchType.setCurrentIndex(0)
            self._ui.searchType.currentIndexChanged.connect(self.loadSortOrFilter)
            self._ui.sortOrFilter.currentIndexChanged.connect(self.setSearchOptions)
            self._ui.refreshChannelButton.clicked.connect(self.refreshChannel)
            Utils.setIconViewer(self._ui.refreshChannelButton, Icons.RELOAD)
            self._ui.refreshVideoListButton.clicked.connect(self.refreshVideoList)
            Utils.setIconViewer(self._ui.refreshVideoListButton, Icons.RELOAD)
            self._ui.openInWebBrowserButton.clicked.connect(self.openInWebBrowser)
            Utils.setIconViewer(self._ui.openInWebBrowserButton, Icons.LAUNCH)
            self.loadSortOrFilter(0)
        else:
            self._ui.tabWidget.setCurrentIndex(1)
            self._ui.tabWidget.tabBar().hide()
            if type(self.data) == TwitchGQLModels.Video:
                videoType = T("video")
                videoId = self.data.id
            else:
                videoType = T("clip")
                videoId = self.data.slug
            self.setWindowTitle(f"{videoType}: {videoId}")
            self._ui.windowTitleLabel.setText(f"{videoType} {T('id')}: {videoId}")
            self._ui.controlArea.hide()
            self.addVideos([self.data])
            self.setLoading(False)

    def refreshChannel(self) -> None:
        self._ui.refreshChannelButton.setEnabled(False)
        App.TwitchGQL.getChannel(login=self.channel.login).finished.connect(self._processChannelRefreshResult)

    def _processChannelRefreshResult(self, response: TwitchGQLAPI.TwitchGQLResponse) -> None:
        if response.getError() == None:
            self.showChannel(response.getData())
        else:
            if isinstance(response.getError(), TwitchGQLAPI.Exceptions.DataNotFound):
                Utils.info("error", "#Channel not found. Deleted or temporary error.", parent=self)
            else:
                Utils.info(*Messages.INFO.NETWORK_ERROR, parent=self)
        self._ui.refreshChannelButton.setEnabled(True)

    def showChannel(self, channel: TwitchGQLModels.Channel) -> None:
        self.channel = channel
        self.setWindowTitle(self.channel.displayName)
        self._ui.windowTitleLabel.setText(T("#{channel}'s channel", channel=self.channel.displayName))
        if self.channel.stream == None:
            self._ui.liveLabel.setText(T("offline"))
            self._ui.viewIcon.hide()
            self._ui.viewerCount.hide()
            content = self.channel
        else:
            self._ui.liveLabel.setText(T("live" if self.channel.stream.isLive() else "rerun"))
            self._ui.viewIcon.show()
            self._ui.viewerCount.show()
            self._ui.viewerCount.setText(self.channel.stream.viewersCount)
            content = self.channel.stream
        sizePolicy = self._ui.viewIcon.sizePolicy()
        sizePolicy.setRetainSizeWhenHidden(True)
        self._ui.viewIcon.setSizePolicy(sizePolicy)
        self._ui.channelMainWidget = Utils.setPlaceholder(self._ui.channelMainWidget, Ui.VideoDownloadWidget(content, parent=self))
        self._ui.channelMainWidget.accountPageShowRequested.connect(self.accountPageShowRequested)
        self._ui.channelMainWidget.setThumbnailImageStyleSheet(f"#thumbnailImage {{background-color: #{self.channel.primaryColorHex or self.DEFAULT_CHANNEL_PRIMARY_COLOR};background-image: url('{Icons.CHANNEL_BACKGROUND_WHITE.path}');background-position: center center;}}")
        self._ui.profileImage.loadImage(filePath=Images.PROFILE_IMAGE, url=self.channel.profileImageURL, urlFormatSize=ImageSize.USER_PROFILE, refresh=True)
        self._ui.displayName.setText(self.channel.displayName)
        sizePolicy = self._ui.verifiedIcon.sizePolicy()
        sizePolicy.setRetainSizeWhenHidden(True)
        self._ui.verifiedIcon.setSizePolicy(sizePolicy)
        self._ui.verifiedIcon.setVisible(self.channel.isVerified)
        self._ui.description.setText(self.channel.description)
        self._ui.followers.setText(T("#{followers} followers", followers=self.channel.followers))
        if self.channel.isPartner:
            broadcasterType = "partner-streamer"
            themeColor = "#9147ff"
        elif self.channel.isAffiliate:
            broadcasterType = "affiliate-streamer"
            themeColor = "#1fac46"
        else:
            broadcasterType = "streamer"
            themeColor = "#000000"
        self._ui.broadcasterType.setText(T(broadcasterType))
        self._ui.broadcasterTypeArea.setStyleSheet(f"color: rgb(255, 255, 255);background-color: {themeColor};border-radius: 10px;")

    def openInWebBrowser(self) -> None:
        Utils.openUrl(self.channel.profileURL)

    def loadSortOrFilter(self, index: int) -> None:
        self._ui.sortOrFilter.clear()
        self._ui.sortOrFilter.addItems([T(item[0]) for item in (self.FILTER_LIST if self.SEARCH_TYPES[index][0] == "clips" else self.SORT_LIST)])
        self._ui.sortOrFilter.setCurrentIndex(0)

    def setSearchOptions(self, index: int) -> None:
        if index == -1:
            return
        self._ui.channelVideosLabel.setText(T("#{channel}'s {searchType}", channel=self.channel.displayName, searchType=T(self.SEARCH_TYPES[self._ui.searchType.currentIndex()][0])))
        self.searchVideos()

    def refreshVideoList(self) -> None:
        self.searchVideos()

    def searchVideos(self, cursor: str = "") -> None:
        if cursor == "":
            self.clearVideoList()
        self.setLoading(True)
        if self.SEARCH_TYPES[self._ui.searchType.currentIndex()][0] == "clips":
            filter = self.FILTER_LIST[self._ui.sortOrFilter.currentIndex()][1]
            App.TwitchGQL.getChannelClips(channel=self.channel.login, filter=filter, cursor=cursor).finished.connect(self._processSearchResult)
        else:
            videoType = self.SEARCH_TYPES[self._ui.searchType.currentIndex()][1]
            sort = self.SORT_LIST[self._ui.sortOrFilter.currentIndex()][1]
            App.TwitchGQL.getChannelVideos(channel=self.channel.login, videoType=videoType, sort=sort, cursor=cursor).finished.connect(self._processSearchResult)

    def _processSearchResult(self, response: TwitchGQLAPI.TwitchGQLResponse) -> None:
        if response.getError() == None:
            self.searchResult = response.getData()
            self.addVideos(self.searchResult.data)
            self.setLoading(False)
        else:
            self.setLoading(False, showErrorMessage=True)
            if isinstance(response.getError(), TwitchGQLAPI.Exceptions.DataNotFound):
                Utils.info("error", "#Channel not found. Deleted or temporary error.", parent=self)
            else:
                Utils.info(*Messages.INFO.NETWORK_ERROR, parent=self)

    def searchMoreVideos(self, value: int) -> None:
        if type(self.data) != TwitchGQLModels.Channel:
            return
        if self.isLoading():
            return
        if self.searchResult.hasNextPage:
            if self._ui.videoArea.verticalScrollBar().maximum() - self.SEARCH_SCROLL_THRESHOLD <= value:
                self.searchVideos(self.searchResult.cursor)

    def addVideos(self, videos: list[TwitchGQLModels.Video | TwitchGQLModels.Clip]) -> None:
        self._widgetListViewer.setAutoReloadEnabled(False)
        for data in videos:
            videoDownloadWidget = Ui.VideoDownloadWidget(data, resizable=False, parent=None)
            videoDownloadWidget.accountPageShowRequested.connect(self.accountPageShowRequested)
            self._widgetListViewer.addWidget(videoDownloadWidget)
        self._widgetListViewer.setAutoReloadEnabled(True)

    def clearVideoList(self) -> None:
        self._widgetListViewer.clear()