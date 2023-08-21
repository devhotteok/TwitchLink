from Core.Ui import *
from Services.Messages import Messages
from Services.Twitch.GQL import TwitchGQLModels
from Search.SearchMode import SearchMode
from Search import ExternalPlaybackGenerator
from Download.DownloadInfo import DownloadInfo


class Home(QtWidgets.QWidget):
    searchResultWindowRequested = QtCore.pyqtSignal(object)

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("home", self)
        self._ui.appLogo.setMargin(10)
        self._ui.appName.setText(Config.APP_NAME)
        self._ui.smartSearchButton.clicked.connect(self.smartSearch)
        self._ui.channelSearchButton.clicked.connect(self.searchChannel)
        self._ui.videoClipSearchButton.clicked.connect(self.searchVideo)
        self._ui.urlSearchButton.clicked.connect(self.searchUrl)
        self._ui.copyright.setText(Config.getCopyrightInfo())

    def smartSearch(self) -> None:
        self.startSearch(SearchMode(SearchMode.Types.UNKNOWN))

    def searchChannel(self) -> None:
        self.startSearch(SearchMode(SearchMode.Types.CHANNEL))

    def searchVideo(self) -> None:
        self.startSearch(SearchMode(SearchMode.Types.VIDEO))

    def searchUrl(self) -> None:
        self.startSearch(SearchMode(SearchMode.Types.URL))

    def startSearch(self, mode: SearchMode) -> None:
        search = Ui.Search(mode, parent=self)
        search.searchCompleted.connect(self.searchCompleted, QtCore.Qt.ConnectionType.QueuedConnection)
        search.exec()

    def searchCompleted(self, result: TwitchGQLModels.Channel | TwitchGQLModels.Video | TwitchGQLModels.Clip | ExternalPlaybackGenerator.ExternalPlayback) -> None:
        if isinstance(result, ExternalPlaybackGenerator.ExternalPlayback):
            if isinstance(result, ExternalPlaybackGenerator.ExternalStreamPlayback):
                data = TwitchGQLModels.Stream({"title": "Unknown Stream", "game": {"name": "Unknown"}, "broadcaster": {"login": "Unknown User"}})
            else:
                data = TwitchGQLModels.Video({"title": "Unknown Video", "game": {"name": "Unknown"}, "owner": {"login": "Unknown User"}, "lengthSeconds": result.totalSeconds})
            downloadMenu = Ui.DownloadMenu(DownloadInfo(data, result), parent=self)
            downloadMenu.downloadRequested.connect(self.startDownload, QtCore.Qt.ConnectionType.QueuedConnection)
            downloadMenu.exec()
        else:
            self.searchResultWindowRequested.emit(result)

    def startDownload(self, downloadInfo: DownloadInfo) -> None:
        try:
            App.DownloadManager.create(downloadInfo)
        except:
            Utils.info(*Messages.INFO.ACTION_PERFORM_ERROR, parent=self)