from .Modes import SearchModes
from .Config import Config

import re


class TwitchQueryParser:
    @classmethod
    def parseQuery(cls, query):
        if re.search(Config.VIDEO_ID_REGEX, query) != None:
            return [
                (SearchModes(SearchModes.VIDEO), query),
                (SearchModes(SearchModes.CHANNEL), query)
            ]
        elif re.search(Config.CHANNEL_ID_REGEX, query) != None:
            return [
                (SearchModes(SearchModes.CHANNEL), query),
                (SearchModes(SearchModes.CLIP), query)
            ]
        elif re.search(Config.CLIP_ID_REGEX, query) != None:
            return [
                (SearchModes(SearchModes.CLIP), query)
            ]
        else:
            scanUrl = []
            check = re.search(Config.VIDEO_URL_REGEX, query)
            if check != None:
                scanUrl.append((SearchModes(SearchModes.VIDEO), check.group(1)))
            check = re.search(Config.CLIP_URL_REGEX, query)
            if check != None:
                scanUrl.append((SearchModes(SearchModes.CLIP), check.group(1)))
            check = re.search(Config.CHANNEL_URL_REGEX, query)
            if check != None:
                scanUrl.append((SearchModes(SearchModes.CHANNEL), check.group(1)))
            return scanUrl or [(SearchModes(SearchModes.UNKNOWN), query)]

    @classmethod
    def parseUrl(cls, url):
        check = re.search(Config.VIDEO_URL_REGEX, url)
        if check != None:
            return SearchModes(SearchModes.VIDEO), check.group(1)
        check = re.search(Config.CLIP_URL_REGEX, url)
        if check != None:
            return SearchModes(SearchModes.CLIP), check.group(1)
        check = re.search(Config.CHANNEL_URL_REGEX, url)
        if check != None:
            return SearchModes(SearchModes.CHANNEL), check.group(1)
        return SearchModes(SearchModes.UNKNOWN), url