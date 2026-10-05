from .TwitchPlaybackModels import TwitchUnavailableResolution

from Services.Playlist.PlaylistTagReader import PlaylistTag
from Services.Playlist.MultivariantPlaylistReader import MultivariantPlaylistReader
from Services.Playlist.Resolution import Resolution

from PyQt6 import QtCore

import base64
import json


class TwitchPlaylistReader:
    @classmethod
    def loads(cls, playlist: str, baseUrl: QtCore.QUrl | None = None) -> tuple[dict[str, Resolution], list[TwitchUnavailableResolution]]:
        multivariantPlaylist = MultivariantPlaylistReader.loads(playlist, baseUrl=baseUrl)
        unavailableResolutions = []
        for tag in multivariantPlaylist.tags.get("EXT-X-SESSION-DATA", []):
            unavailableResolutions.extend(cls._parseUnavailableResolutionsTag(tag))
        return multivariantPlaylist.resolutions, unavailableResolutions

    @classmethod
    def _parseUnavailableResolutionsTag(cls, tag: PlaylistTag) -> list[TwitchUnavailableResolution]:
        if not isinstance(tag.data, dict) or tag.data.get("DATA-ID") != "com.amazon.ivs.unavailable-media":
            return []
        try:
            data = json.loads(base64.b64decode(tag.data["VALUE"], validate=True).decode(errors="ignore"))
        except:
            return []
        if not isinstance(data, list):
            return []
        resolutions = []
        for item in data:
            if isinstance(item, dict):
                resolution = cls._parseUnavailableResolution(item)
                if resolution != None:
                    resolutions.append(resolution)
        return resolutions

    @classmethod
    def _parseUnavailableResolution(cls, data: dict) -> TwitchUnavailableResolution | None:
        authorizationReasons = data.get("AUTHORIZATION_REASONS", [])
        filterReasons = data.get("FILTER_REASONS", [])
        authorizationReasons = [reason for reason in authorizationReasons if isinstance(reason, str) and reason != ""] if isinstance(authorizationReasons, list) else []
        filterReasons = [reason for reason in filterReasons if isinstance(reason, str) and reason != ""] if isinstance(filterReasons, list) else []
        return TwitchUnavailableResolution(
            name=data.get("NAME", ""),
            groupId=data.get("GROUP-ID", ""),
            authorizationReasons=authorizationReasons,
            filterReasons=filterReasons
        )