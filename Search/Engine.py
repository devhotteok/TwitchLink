from .SearchMode import SearchMode
from .QueryParser import TwitchQueryParser
from . import ExternalPlaybackGenerator

from Core import App
from Core import GlobalExceptions
from Services.Twitch.GQL import TwitchGQLAPI
from Services.Twitch.GQL import TwitchGQLModels

from PyQt6 import QtCore


class Exceptions(GlobalExceptions.Exceptions):
    class InvalidURL(Exception):
        def __str__(self):
            return "Invalid URL"

    class ChannelNotFound(Exception):
        def __str__(self):
            return "Channel Not Found"

    class VideoNotFound(Exception):
        def __str__(self):
            return "Video Not Found"

    class ClipNotFound(Exception):
        def __str__(self):
            return "Clip Not Found"

    class NoResultsFound(Exception):
        def __str__(self):
            return "No Results Found"


class SearchEngine(QtCore.QObject):
    finished = QtCore.pyqtSignal(object)

    def __init__(self, mode: SearchMode, query: str, searchExternalContent: bool = False, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._mode = mode
        self._query = query
        self._searchExternalContent = searchExternalContent
        self._multipleSearch: list[tuple[SearchMode, str]] | None = None
        self._error: Exception | None = None
        self._data: TwitchGQLModels.Channel | TwitchGQLModels.Video | TwitchGQLModels.Clip | ExternalPlaybackGenerator.ExternalPlayback | None = None
        self._parseQuery()

    def _parseQuery(self) -> None:
        if self._mode.isUnknown():
            self._multipleSearch = TwitchQueryParser.parseQuery(self._query)
        elif self._mode.isUrl():
            self._mode, self._query = TwitchQueryParser.parseUrl(self._query)
        self._search()

    def _search(self) -> None:
        if self._multipleSearch != None:
            self._mode, self._query = self._multipleSearch.pop(0)
        if self._mode.isChannel():
            App.TwitchGQL.getChannel(login=self._query).finished.connect(self._searchFinished)
        elif self._mode.isVideo():
            App.TwitchGQL.getVideo(id=self._query).finished.connect(self._searchFinished)
        elif self._mode.isClip():
            App.TwitchGQL.getClip(slug=self._query).finished.connect(self._searchFinished)
        elif self._searchExternalContent:
            ExternalPlaybackGenerator.ExternalPlaybackGenerator(QtCore.QUrl(self._query), parent=self).finished.connect(self._externalPlaybackSearchFinished)
        else:
            self._raiseException(Exceptions.InvalidURL())

    def _searchFinished(self, response: TwitchGQLAPI.TwitchGQLResponse) -> None:
        if response.getError() == None:
            self._data = response.getData()
            self._setFinished()
        elif self._multipleSearch == None:
            if self._mode.isChannel():
                self._raiseException(Exceptions.ChannelNotFound())
            elif self._mode.isVideo():
                self._raiseException(Exceptions.VideoNotFound())
            else:
                self._raiseException(Exceptions.ClipNotFound())
        elif len(self._multipleSearch) != 0:
            self._search()
        else:
            self._raiseException(Exceptions.NoResultsFound())

    def _externalPlaybackSearchFinished(self, generator: ExternalPlaybackGenerator.ExternalPlaybackGenerator) -> None:
        if generator.getError() == None:
            self._data = generator.getData()
            self._setFinished()
        else:
            self._raiseException(Exceptions.InvalidURL())

    def _setFinished(self) -> None:
        self.finished.emit(self)
        self.deleteLater()

    def _raiseException(self, exception: Exception) -> None:
        self._error = exception
        self._setFinished()

    def getError(self) -> Exception:
        return self._error

    def getData(self) -> TwitchGQLModels.Channel | TwitchGQLModels.Video | TwitchGQLModels.Clip | ExternalPlaybackGenerator.ExternalPlayback:
        return self._data