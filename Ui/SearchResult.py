from Core.App import App
from Core.Ui import *
from Search import Engine
from Services.Messages import Messages
from Services.Utils.ResizableGrid import ResizableGrid
from Services.Twitch.Gql import TwitchGqlModels
from Download.DownloadManager import DownloadManager


class SearchResult(QtWidgets.QDialog, UiFile.searchResult):
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

    def __init__(self, data):
        super().__init__(parent=App.getActiveWindow())
        self.setWindowFlag(QtCore.Qt.WindowMaximizeButtonHint)
        self.videoList = ResizableGrid(self.videoArea.layout())
        self.videoWidgetWidth = Ui.VideoDownloadWidget(self, None, resizable=False).minimumSizeHint().width()
        self.allocatedWidth = self.scrollArea.verticalScrollBar().sizeHint().width() + self.scrollAreaContents.layout().contentsMargins().left() + self.scrollAreaContents.layout().contentsMargins().right()
        self.scrollArea.setMinimumWidth(self.videoWidgetWidth + self.allocatedWidth)
        self.scrollArea.showEvent = Utils.hook(self.scrollArea.showEvent, self.hookEventCalcColumn)
        self.scrollArea.resizeEvent = Utils.hook(self.scrollArea.resizeEvent, self.hookEventCalcColumn)
        self.scrollArea.verticalScrollBar().valueChanged.connect(self.searchMoreVideos)
        self.setDownloadEnabled(True)
        self.data = data
        self.setup()
        self.downloaderId = None
        self.downloader = None

    def hookEventCalcColumn(self, originalFunction):
        self.calcColumn()
        return originalFunction()

    def calcColumn(self):
        column = (self.scrollArea.width() - self.allocatedWidth) // self.videoWidgetWidth
        if self.videoList.getColumn() != column:
            self.scrollArea.verticalScrollBar().setValue(0)
            self.videoList.setColumn(column)

    def setDownloadEnabled(self, enabled):
        self.downloadEnabled = enabled
        if hasattr(self, "channel"):
            if self.channel.stream != None:
                self.channelMainWidget.setEnabled(enabled)
        self.scrollArea.setEnabled(self.downloadEnabled)

    def setLoading(self, loading):
        self.loading = loading
        if self.loading:
            self.searchType.setEnabled(False)
            self.sortOrFilter.setEnabled(False)
            self.statusLabel.setText(T("loading", ellipsis=True))
            self.loadingLabel.show()
        else:
            self.searchType.setEnabled(True)
            self.sortOrFilter.setEnabled(True)
            self.statusLabel.setText(T("no-results-found"))
            self.loadingLabel.hide()

    def setup(self):
        if type(self.data) == TwitchGqlModels.Channel:
            self.channel = self.data
            self.window_title.setText(T("#{channel}'s channel", channel=self.data.displayName))
            self.showChannel()
            self.searchType.addItems(list(map(lambda item: T(item[0]), self.SEARCH_TYPES)))
            self.searchType.setCurrentIndex(0)
            self.searchType.currentIndexChanged.connect(self.loadSortOrFilter)
            self.sortOrFilter.currentIndexChanged.connect(self.setSearchOptions)
            self.loadSortOrFilter(0)
        else:
            self.tabWidget.setTabVisible(0, False)
            self.window_title.setText(T("#Video ID : {id}", id=self.data.id) if type(self.data) == TwitchGqlModels.Video else T("#Clip ID : {slug}", slug=self.data.slug))
            self.controlArea.hide()
            self.addVideos([self.data])
            self.setLoading(False)
        self.progressArea.hide()

    def showChannel(self):
        if self.channel.stream == None:
            self.liveLabel.setText(T("offline"))
            self.viewer_count.hide()
            videoData = self.channel
        else:
            self.liveLabel.setText(T("live"))
            self.viewer_count.setText(T("#{viewer} viewers", viewer=self.channel.stream.viewersCount))
            videoData = self.channel.stream
        self.channelMainWidget = Ui.VideoDownloadWidget(self, videoData)
        Utils.setPlaceholder(self.channelMainWidgetPlaceholder, self.channelMainWidget)
        self.profileImageLoader = Utils.ImageLoader(self.profile_image, self.channel.profileImageURL, Config.PROFILE_IMAGE, preferredSize=(600, 600), refresh=True)
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

    def loadSortOrFilter(self, index):
        self.sortOrFilter.clear()
        self.sortOrFilter.addItems(list(map(lambda item: T(item[0]), self.FILTER_LIST if self.SEARCH_TYPES[index][0] == "clips" else self.SORT_LIST)))
        self.sortOrFilter.setCurrentIndex(0)

    def setSearchOptions(self, index):
        if index == -1:
            return
        self.channelVideosLabel.setText(T("#{channel}'s {searchType}", channel=self.channel.displayName, searchType=T(self.SEARCH_TYPES[self.searchType.currentIndex()][0])))
        self.searchVideos()

    def searchVideos(self, cursor=""):
        self.setLoading(True)
        if cursor == "":
            self.clearVideoList()
        if self.SEARCH_TYPES[self.searchType.currentIndex()][0] == "clips":
            filter = self.FILTER_LIST[self.sortOrFilter.currentIndex()][1]
            self.searchThread = Engine.SearchThread(
                target=Engine.Search.ChannelClips,
                callback=self.processSearchResult,
                args=(self.channel.login, filter, cursor)
            )
        else:
            videoType = self.SEARCH_TYPES[self.searchType.currentIndex()][1]
            sort = self.SORT_LIST[self.sortOrFilter.currentIndex()][1]
            self.searchThread = Engine.SearchThread(
                target=Engine.Search.ChannelVideos,
                callback=self.processSearchResult,
                args=(self.channel.login, videoType, sort, cursor)
            )

    def processSearchResult(self, result):
        if result.success:
            self.searchResult = result.data
            self.addVideos(self.searchResult.data)
            self.setLoading(False)
        else:
            self.setLoading(False)
            if result.error == Engine.Exceptions.ChannelNotFound:
                Utils.info("error", "#Channel not found. Deleted or temporary error.")
            else:
                Utils.info(*Messages.INFO.NETWORK_ERROR)

    def searchMoreVideos(self, value):
        if type(self.data) != TwitchGqlModels.Channel:
            return
        if self.loading:
            return
        if self.searchResult.hasNextPage:
            if (self.scrollArea.verticalScrollBar().maximum() - value) < self.SEARCH_SCROLL_POSITION:
                self.searchVideos(self.searchResult.cursor)

    def addVideos(self, videos):
        for data in videos:
            self.videoList.addWidget(Ui.VideoDownloadWidget(self, data, resizable=False))
            if len(self.videoList.widgets) % 6 == 1:
                if AdManager.Config.SHOW:
                    self.videoList.addWidget(AdManager.Ad(minimumSize=QtCore.QSize(300, 250), responsive=False))
        self.reloadVideoAreaStatus()

    def clearVideoList(self):
        self.scrollArea.verticalScrollBar().setValue(0)
        self.videoList.clearAll()
        self.reloadVideoAreaStatus()

    def reloadVideoAreaStatus(self):
        noWidget = len(self.videoList.widgets) == 0
        self.videoArea.setVisible(not noWidget)
        self.statusLabel.setVisible(noWidget)

    def askDownload(self, downloadInfo):
        downloadInfo = Ui.DownloadMenu(downloadInfo).exec()
        if downloadInfo != False:
            self.accept(downloadInfo)

    def downloadStream(self, downloadInfo):
        self.askDownload(downloadInfo)

    def downloadVideo(self, downloadInfo):
        self.askDownload(downloadInfo)

    def downloadClip(self, downloadInfo):
        downloadInfo = Ui.DownloadMenu(downloadInfo).exec()
        if downloadInfo != False:
            self.setDownloadEnabled(False)
            self.downloaderId = DownloadManager.start(downloadInfo)
            self.downloader = DownloadManager.get(self.downloaderId)
            self.connectDownloader()

    def connectDownloader(self):
        self.downloader.statusUpdate.connect(self.handleClipStatus)
        self.downloader.progressUpdate.connect(self.handleClipProgress)
        self.downloader.finished.connect(self.handleDownloadResult)
        self.handleClipProgress(self.downloader.progress)
        self.handleClipStatus(self.downloader.status)

    def disconnectDownloader(self):
        self.downloader.statusUpdate.disconnect(self.handleClipStatus)
        self.downloader.progressUpdate.disconnect(self.handleClipProgress)
        self.downloader.finished.disconnect(self.handleDownloadResult)

    def handleClipProgress(self, progress):
        self.clipProgress(downloadProgress=progress.byteSizeProgress)

    def clipProgress(self, downloadProgress=0):
        self.progressLabel.setText(T("downloading", ellipsis=True))
        self.downloadingProgress.setValue(downloadProgress)
        self.downloadingProgress.show()
        self.progressArea.show()

    def handleDownloadResult(self):
        self.setDownloadEnabled(True)
        self.progressArea.hide()
        if self.downloader.status.getError() == None:
            self.progressLabel.setText(T("download-complete"))
        else:
            self.progressLabel.setText(T("download-failed"))
        self.disconnectDownloader()
        DownloadManager.remove(self.downloaderId)

    def closeEvent(self, event):
        if self.downloader != None:
            if self.downloader.isRunning():
                Utils.info("warning", "#There is a download in progress.")
                return event.ignore()
        return super().closeEvent(event)