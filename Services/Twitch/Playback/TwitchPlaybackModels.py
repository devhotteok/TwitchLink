from Services.Twitch.GQL import TwitchGQLModels
from Services.Playlist.Resolution import Resolution
from AppData.EncoderDecoder import Serializable

from PyQt6 import QtCore


class TwitchPlaybackObject(Serializable):
    SERIALIZABLE_INIT_MODEL = False
    SERIALIZABLE_STRICT_MODE = False

    def __str__(self):
        return f"<{self.__class__.__name__} {self.__dict__}>"

    def __repr__(self):
        return self.__str__()


class TwitchUnavailableResolution(Resolution):
    def __init__(self, name: str, groupId: str, authorizationReasons: list[str], filterReasons: list[str]):
        super().__init__(name, groupId, QtCore.QUrl(), False, False)
        self.authorizationReasons = authorizationReasons
        self.filterReasons = filterReasons

    def isLoginRequired(self) -> bool:
        return "AUTHZ_NOT_LOGGED_IN" in self.authorizationReasons


class TwitchStreamPlayback(TwitchPlaybackObject):
    def __init__(self, login: str, token: TwitchGQLModels.StreamPlaybackAccessToken, resolutions: dict[str, Resolution], unavailableResolutions: list[TwitchUnavailableResolution] | None = None):
        self.login = login
        self.token = token
        self.resolutions = resolutions
        self.unavailableResolutions = unavailableResolutions or []

    def resolution(self, id: str) -> Resolution | None:
        if id in self.resolutions:
            return self.resolutions[id]
        else:
            return None

    def getAvailableResolutions(self) -> list[Resolution]:
        return sorted(self.resolutions.values(), reverse=True)

    def getUnavailableResolutions(self) -> list[TwitchUnavailableResolution]:
        return sorted(self.unavailableResolutions, reverse=True)

    def getAllResolutions(self) -> list[Resolution | TwitchUnavailableResolution]:
        return sorted([*self.resolutions.values(), *self.unavailableResolutions], reverse=True)


class TwitchVideoPlayback(TwitchPlaybackObject):
    def __init__(self, id: str, token: TwitchGQLModels.VideoPlaybackAccessToken, resolutions: dict[str, Resolution], unavailableResolutions: list[TwitchUnavailableResolution] | None = None):
        self.id = id
        self.token = token
        self.resolutions = resolutions
        self.unavailableResolutions = unavailableResolutions or []

    def resolution(self, id: str) -> Resolution | None:
        if id in self.resolutions:
            return self.resolutions[id]
        else:
            return None

    def getAvailableResolutions(self) -> list[Resolution]:
        return sorted(self.resolutions.values(), reverse=True)

    def getUnavailableResolutions(self) -> list[TwitchUnavailableResolution]:
        return sorted(self.unavailableResolutions, reverse=True)

    def getAllResolutions(self) -> list[Resolution | TwitchUnavailableResolution]:
        return sorted([*self.resolutions.values(), *self.unavailableResolutions], reverse=True)


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

    def getAvailableResolutions(self) -> list[Resolution]:
        return sorted(self.resolutions.values(), reverse=True)

    def getUnavailableResolutions(self) -> list[TwitchUnavailableResolution]:
        return []

    def getAllResolutions(self) -> list[Resolution | TwitchUnavailableResolution]:
        return self.getAvailableResolutions()