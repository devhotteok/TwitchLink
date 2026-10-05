from .PlaylistTagReader import PlaylistTagReader
from .MultivariantPlaylist import MultivariantPlaylist
from .Resolution import Resolution

from PyQt6 import QtCore


class MultivariantPlaylistReader(PlaylistTagReader):
    @classmethod
    def loads(cls, playlist: str, baseUrl: QtCore.QUrl | None = None) -> MultivariantPlaylist:
        tags = {}
        resolutions = []
        expectedMedia: dict[str, str] | None = None
        expectedStream: dict[str, str] | None = None
        for line in playlist.splitlines():
            tag = cls.getTag(line)
            if tag != None:
                if tag.name not in tags:
                    tags[tag.name] = []
                tags[tag.name].append(tag)
                if tag.name == "EXT-X-MEDIA" and isinstance(tag.data, dict):
                    expectedMedia = tag.data
                elif tag.name == "EXT-X-STREAM-INF" and isinstance(tag.data, dict):
                    expectedStream = tag.data
                continue
            if expectedStream != None:
                resolutions.append(cls.generateResolution(expectedMedia or {}, expectedStream, QtCore.QUrl(line) if baseUrl == None else baseUrl.resolved(QtCore.QUrl(line))))
                expectedMedia = None
                expectedStream = None
                continue
        return MultivariantPlaylist(
            tags=tags,
            resolutions={resolution.groupId: resolution for resolution in sorted(resolutions, reverse=True)}
        )

    @classmethod
    def generateResolution(cls, mediaData: dict[str, str], streamData: dict[str, str], url: QtCore.QUrl) -> Resolution:
        return Resolution(
            name=mediaData.get("NAME", ""),
            groupId=mediaData.get("GROUP-ID", ""),
            url=url,
            autoSelect=mediaData.get("AUTOSELECT", "") == "YES",
            default=mediaData.get("DEFAULT", "") == "YES"
        )