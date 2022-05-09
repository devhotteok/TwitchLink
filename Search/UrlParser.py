from .Modes import SearchModes
from .Config import Config

import re


class TwitchUrlParser:
    def __init__(self, url):
        self.type, self.data = self.parseUrl(url)

    def parseUrl(self, url):
        check = re.search(Config.VIDEO_URL_REGEX, url)
        if check != None:
            return SearchModes(SearchModes.VIDEO), check.group(1)
        check = re.search(Config.CLIP_URL_REGEX, url)
        if check != None:
            return SearchModes(SearchModes.CLIP), check.group(1)
        check = re.search(Config.CHANNEL_URL_REGEX, url)
        if check != None:
            return SearchModes(SearchModes.CHANNEL), check.group(1)
        return None, url