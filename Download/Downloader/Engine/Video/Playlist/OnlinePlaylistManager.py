from .PlaylistManager import PlaylistManager

from Core.GlobalExceptions import Exceptions
from Services.NetworkRequests import Network


class OnlinePlaylistManager(PlaylistManager):
    def __init__(self, url, filePath, strictMode=False):
        self.url = url
        super(OnlinePlaylistManager, self).__init__(self.getOnlinePlaylist(), filePath, strictMode=strictMode)

    def getOnlinePlaylist(self):
        try:
            data = Network.session.get(self.url)
            if data.status_code != 200:
                raise
            return data.text
        except:
            raise Exceptions.NetworkError

    def updatePlaylist(self):
        super().readPlaylist(self.getOnlinePlaylist())