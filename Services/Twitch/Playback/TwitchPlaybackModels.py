from Services.Twitch.GQL import TwitchGQLModels
from Services.Playlist.Resolution import Resolution
from AppData.EncoderDecoder import Serializable


class TwitchPlaybackObject(Serializable):
    SERIALIZABLE_INIT_MODEL = False
    SERIALIZABLE_STRICT_MODE = False

    def __str__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"

    def __repr__(self):
        return self.__str__()


class TwitchStreamPlayback(TwitchPlaybackObject):
    def __init__(self, login: str, token: TwitchGQLModels.StreamPlaybackAccessToken, resolutions: dict[str, Resolution]):
        self.login = login
        self.token = token
        self.resolutions = resolutions

    def resolution(self, id: str) -> Resolution | None:
        if id in self.resolutions:
            return self.resolutions[id]
        else:
            return None

    def getResolutions(self) -> list[Resolution]:
        return list(self.resolutions.values())


class TwitchVideoPlayback(TwitchPlaybackObject):
    def __init__(self, id: str, token: TwitchGQLModels.VideoPlaybackAccessToken, resolutions: dict[str, Resolution]):
        self.id = id
        self.token = token
        self.resolutions = resolutions

    def resolution(self, id: str) -> Resolution | None:
        if id in self.resolutions:
            return self.resolutions[id]
        else:
            return None

    def getResolutions(self) -> list[Resolution]:
        return list(self.resolutions.values())


class TwitchClipPlayback(TwitchPlaybackObject):
    def __init__(self, slug: str, token: TwitchGQLModels.ClipPlaybackAccessToken, resolutions: dict[str, Resolution]):
        self.slug = slug
        self.token = token
        self.resolutions = resolutions

    def resolution(self, id: str) -> Resolution | None:
        if id in self.resolutions:
            return self.resolutions[id]
        else:
            return None

    def getResolutions(self) -> list[Resolution]:
        return list(self.resolutions.values())