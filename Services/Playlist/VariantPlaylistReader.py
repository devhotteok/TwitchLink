from .PlaylistTagReader import PlaylistTagReader
from .Resolution import Resolution

from PyQt6 import QtCore


class VariantPlaylistReader(PlaylistTagReader):
    @classmethod
    def loads(cls, playlist: str, baseUrl: QtCore.QUrl | None = None) -> dict[str, Resolution]:
        resolutions = []
        expect = False
        for line in playlist.splitlines():
            tag = cls.getTag(line)
            if tag != None:
                if tag.name == "EXT-X-MEDIA":
                    expect = tag.data
                continue
            if expect != False:
                resolutions.append(cls.generateResolution(expect, QtCore.QUrl(line) if baseUrl == None else baseUrl.resolved(QtCore.QUrl(line))))
                expect = False
                continue
        return {resolution.groupId: resolution for resolution in sorted(resolutions, reverse=True)}

    @classmethod
    def generateResolution(cls, data: dict[str, str], url: QtCore.QUrl) -> Resolution:
        return Resolution(
            name=data.get("NAME", ""),
            groupId=data.get("GROUP-ID", ""),
            url=url,
            autoSelect=data.get("AUTOSELECT", "") == "YES",
            default=data.get("DEFAULT", "") == "YES"
        )