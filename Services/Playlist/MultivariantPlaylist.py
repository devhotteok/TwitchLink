from .PlaylistTagReader import PlaylistTag
from .Resolution import Resolution


class MultivariantPlaylist:
    def __init__(self, tags: dict[str, list[PlaylistTag]], resolutions: dict[str, Resolution]):
        self.tags: dict[str, list[PlaylistTag]] = tags
        self.resolutions: dict[str, Resolution] = resolutions