from Core.App import App
from Core.Ui import *
from Services.Twitch.Gql import TwitchGqlModels
from Search.Modes import SearchModes
from Search import PlaylistAccessToken
from Download.DownloadInfo import DownloadInfo
from Download.DownloadManager import DownloadManager


class Home(QtWidgets.QWidget, UiFile.home):
    def __init__(self):
        super().__init__()
        self.appLogo.setContentsMargins(10, 10, 10, 10)
        self.appLogoLoader = Utils.ImageLoader(self.appLogo, Config.LOGO_IMAGE)
        self.appName.setText(Config.APP_NAME)
        self.channel_id.clicked.connect(self.searchChannel)
        self.video_id.clicked.connect(self.searchVideo)
        self.video_url.clicked.connect(self.searchUrl)
        self.copyright.setText(Config.getCopyrightInfo())

    def searchChannel(self):
        self.startSearch(SearchModes.CHANNEL())

    def searchVideo(self):
        self.startSearch(SearchModes.VIDEO())

    def searchUrl(self):
        self.startSearch(SearchModes.URL())

    def startSearch(self, mode):
        searchResult = Ui.Search(mode).exec()
        if searchResult != False:
            if type(searchResult) == PlaylistAccessToken.TwitchPlaylist:
                if searchResult.type.isStream():
                    data = TwitchGqlModels.Stream({"title": "Unknown Stream"})
                else:
                    data = TwitchGqlModels.Video({"title": "Unknown Video", "lengthSeconds": searchResult.totalSeconds})
                downloadInfo = Ui.DownloadMenu(DownloadInfo(data, searchResult), showMore=False).exec()
                if downloadInfo != False:
                    downloaderId = DownloadManager.start(
                        downloadInfo,
                        unmuteVideo=DB.download.isUnmuteVideoEnabled(),
                        updateTrack=DB.download.isUpdateTrackEnabled()
                    )
                    App.coreWindow().showDownload(downloaderId)
            else:
                self.startVideoList(searchResult)

    def startVideoList(self, data):
        downloadInfo = Ui.SearchResult(data).exec()
        if downloadInfo != False:
            downloaderId = DownloadManager.start(
                downloadInfo,
                unmuteVideo=DB.download.isUnmuteVideoEnabled(),
                updateTrack=DB.download.isUpdateTrackEnabled()
            )
            App.coreWindow().showDownload(downloaderId)