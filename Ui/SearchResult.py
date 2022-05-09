from Core.Ui import *
from Search import Engine
from Services.Messages import Messages
from Services.Twitch.Gql import TwitchGqlModels


class SearchResult(QtWidgets.QWidget, UiFile.searchResult):
    accountPageShowRequested = QtCore.pyqtSignal()

    CHANNEL_URL = "https://twitch.tv/{login}"

    SEARCH_SCROLL_POSITION = 300

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

    def __init__(self, data, parent=None):
        super(SearchResult, self).__init__(parent=parent)
        self.data = data
        self.viewIcon = Utils.setSvgIcon(self.viewIcon, Icons.VIEWER_ICON)
        self.infoIcon = Utils.setSvgIcon(self.infoIcon, Icons.INFO_ICON)
        self.setup()
        self.stackedWidget.setStyleSheet(f"#stackedWidget {{background-color: {self.videoArea.palette().color(QtGui.QPalette.Window).name()};}}")
        self.videoArea.setStyleSheet("#videoArea {background-color: transparent;}")
        self.videoArea.verticalScrollBar().setSingleStep(30)
        self.videoArea.verticalScrollBar().valueChanged.connect(self.searchMoreVideos)

    def setLoading(self, loading):
        self.loading = loading
        if self.isLoading():
            self.searchType.setEnabled(False)
            self.sortOrFilter.setEnabled(False)
            self.refreshVideoListButton.setEnabled(False)
            self.statusLabel.setText(T("loading", ellipsis=True))
            self.loadingLabel.show()
        else:
            self.searchType.setEnabled(True)
            self.sortOrFilter.setEnabled(True)
            self.refreshVideoListButton.setEnabled(True)
            self.statusLabel.setText(T("no-results-found"))
            self.loadingLabel.hide()
        if self.videoArea.count() == 0:
            self.stackedWidget.setCurrentIndex(0)
        else:
            self.stackedWidget.setCurrentIndex(1)

    def isLoading(self):
        return self.loading

    def setup(self):
        if type(self.data) == TwitchGqlModels.Channel:
            self.showChannel(self.data)
            self.searchType.addItems([T(item[0]) for item in self.SEARCH_TYPES])
            self.searchType.setCurrentIndex(0)
            self.searchType.currentIndexChanged.connect(self.loadSortOrFilter)
            self.sortOrFilter.currentIndexChanged.connect(self.setSearchOptions)
            self.refreshChannelButton.clicked.connect(self.refreshChannel)
            self.refreshChannelThread = Utils.WorkerThread(parent=self)
            self.refreshChannelThread.resultSignal.connect(self.processChannelRefreshResult)
            self.refreshVideoListButton.clicked.connect(self.refreshVideoList)
            self.searchThread = Utils.WorkerThread(parent=self)
            self.searchThread.resultSignal.connect(self.processSearchResult)
            self.openInWebBrowserButton.clicked.connect(self.openInWebBrowser)
            self.loadSortOrFilter(0)
        else:
            self.tabWidget.setCurrentIndex(1)
            self.tabWidget.tabBar().hide()
            if type(self.data) == TwitchGqlModels.Video:
                videoType = T("video")
                videoId = self.data.id
            else:
                videoType = T("clip")
                videoId = self.data.slug
            self.setWindowTitle(f"{videoType}: {videoId}")
            self.window_title.setText(f"{videoType} {T('id')}: {videoId}")
            self.controlArea.hide()
            self.addVideos([self.data])
            self.setLoading(False)

    def refreshChannel(self):
        self.refreshChannelButton.setEnabled(False)
        self.refreshChannelThread.setup(
            target=Engine.Search.Channel,
            args=(self.channel.login,)
        )
        self.refreshChannelThread.start()

    def processChannelRefreshResult(self, result):
        if result.success:
            self.showChannel(result.data)
        else:
            if isinstance(result.error, Engine.Exceptions.ChannelNotFound):
                self.info("unable-to-download", "#Channel not found. Deleted or temporary error.")
            else:
                self.info(*Messages.INFO.NETWORK_ERROR)
        self.refreshChannelButton.setEnabled(True)

    def showChannel(self, channel):
        self.channel = channel
        self.setWindowTitle(self.channel.displayName)
        self.window_title.setText(T("#{channel}'s channel", channel=self.channel.displayName))
        if self.channel.stream == None:
            self.liveLabel.setText(T("offline").upper())
            self.viewIcon.hide()
            self.viewer_count.hide()
            videoData = self.channel
        else:
            self.liveLabel.setText(T("live" if self.channel.stream.isLive() else "rerun").upper())
            self.viewIcon.show()
            self.viewer_count.show()
            self.viewer_count.setText(self.channel.stream.viewersCount)
            videoData = self.channel.stream
        self.channelMainWidget = Utils.setPlaceholder(self.channelMainWidget, Ui.VideoDownloadWidget(videoData, parent=self))
        self.channelMainWidget.accountPageShowRequested.connect(self.accountPageShowRequested.emit)
        self.profile_image.loadImage(filePath=Images.PROFILE_IMAGE, url=self.channel.profileImageURL, urlFormatSize=ImageSize.USER_PROFILE, refresh=True)
        self.display_name.setText(self.channel.displayName)
        self.description.setText(self.channel.description)
        self.followers.setText(T("#{followers} followers", followers=self.channel.followers))
        if self.channel.isPartner:
            broadcasterType = "partner-streamer"
        elif self.channel.isAffiliate:
            broadcasterType = "affiliate-streamer"
        else:
            broadcasterType = "streamer"
        self.broadcaster_type.setText(T(broadcasterType))

    def openInWebBrowser(self):
        Utils.openUrl(self.CHANNEL_URL.format(login=self.channel.login))

    def loadSortOrFilter(self, index):
        self.sortOrFilter.clear()
        self.sortOrFilter.addItems([T(item[0]) for item in (self.FILTER_LIST if self.SEARCH_TYPES[index][0] == "clips" else self.SORT_LIST)])
        self.sortOrFilter.setCurrentIndex(0)

    def setSearchOptions(self, index):
        if index == -1:
            return
        self.channelVideosLabel.setText(T("#{channel}'s {searchType}", channel=self.channel.displayName, searchType=T(self.SEARCH_TYPES[self.searchType.currentIndex()][0])))
        self.searchVideos()

    def refreshVideoList(self):
        self.searchVideos()

    def searchVideos(self, cursor=""):
        if cursor == "":
            self.clearVideoList()
        self.setLoading(True)
        if self.SEARCH_TYPES[self.searchType.currentIndex()][0] == "clips":
            filter = self.FILTER_LIST[self.sortOrFilter.currentIndex()][1]
            self.searchThread.setup(
                target=Engine.Search.ChannelClips,
                args=(self.channel.login, filter, cursor)
            )
        else:
            videoType = self.SEARCH_TYPES[self.searchType.currentIndex()][1]
            sort = self.SORT_LIST[self.sortOrFilter.currentIndex()][1]
            self.searchThread.setup(
                target=Engine.Search.ChannelVideos,
                args=(self.channel.login, videoType, sort, cursor)
            )
        self.searchThread.start()

    def processSearchResult(self, result):
        if result.success:
            self.searchResult = result.data
            self.addVideos(self.searchResult.data)
            self.setLoading(False)
        else:
            self.setLoading(False)
            if isinstance(result.error, Engine.Exceptions.ChannelNotFound):
                self.info("error", "#Channel not found. Deleted or temporary error.")
            else:
                self.info(*Messages.INFO.NETWORK_ERROR)

    def searchMoreVideos(self, value):
        if type(self.data) != TwitchGqlModels.Channel:
            return
        if self.isLoading():
            return
        if self.searchResult.hasNextPage:
            if (self.videoArea.verticalScrollBar().maximum() - value) < self.SEARCH_SCROLL_POSITION:
                self.searchVideos(self.searchResult.cursor)

    def addVideos(self, videos):
        for data in videos:
            videoDownloadWidget = Ui.VideoDownloadWidget(data, resizable=False, parent=self)
            videoDownloadWidget.accountPageShowRequested.connect(self.accountPageShowRequested.emit)
            self.addWidget(videoDownloadWidget)
            if AdManager.Config.SHOW:
                if self.videoArea.count() % 6 == 1:
                    self.addWidget(AdManager.Ad(minimumSize=videoDownloadWidget.sizeHint(), responsive=False, parent=self), fitContent = False)

    def addWidget(self, widget, fitContent=True):
        widget.setContentsMargins(10, 10, 10, 10)
        item = QtWidgets.QListWidgetItem(parent=self.videoArea)
        item.setSizeHint(widget.sizeHint())
        if fitContent:
            self.videoArea.setMinimumWidth(item.sizeHint().width() + self.videoArea.verticalScrollBar().sizeHint().width())
        self.videoArea.setItemWidget(item, widget)

    def clearVideoList(self):
        self.videoArea.verticalScrollBar().setValue(0)
        self.videoArea.clear()