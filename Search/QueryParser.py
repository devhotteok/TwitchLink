from .SearchMode import SearchMode
from .Config import Config

import re


class TwitchQueryParser:
    @classmethod
    def parseQuery(cls, query: str) -> list[tuple[SearchMode, str]]:
        if re.search(Config.VIDEO_ID_REGEX, query) != None:
            return [
                (SearchMode(SearchMode.Types.VIDEO), query),
                (SearchMode(SearchMode.Types.CHANNEL), query)
            ]
        elif re.search(Config.CHANNEL_ID_REGEX, query) != None:
            return [
                (SearchMode(SearchMode.Types.CHANNEL), query),
                (SearchMode(SearchMode.Types.CLIP), query)
            ]
        elif re.search(Config.CLIP_ID_REGEX, query) != None:
            return [
                (SearchMode(SearchMode.Types.CLIP), query)
            ]
        else:
            scanUrl = []
            check = re.search(Config.VIDEO_URL_REGEX, query)
            if check != None:
                scanUrl.append((SearchMode(SearchMode.Types.VIDEO), check.group(1)))
            check = re.search(Config.CLIP_URL_REGEX, query)
            if check != None:
                scanUrl.append((SearchMode(SearchMode.Types.CLIP), check.group(1)))
            check = re.search(Config.CHANNEL_URL_REGEX, query)
            if check != None:
                scanUrl.append((SearchMode(SearchMode.Types.CHANNEL), check.group(1)))
            return scanUrl or [(SearchMode(SearchMode.Types.UNKNOWN), query)]

    @classmethod
    def parseUrl(cls, url: str) -> tuple[SearchMode, str]:
        check = re.search(Config.VIDEO_URL_REGEX, url)
        if check != None:
            return SearchMode(SearchMode.Types.VIDEO), check.group(1)
        check = re.search(Config.CLIP_URL_REGEX, url)
        if check != None:
            return SearchMode(SearchMode.Types.CLIP), check.group(1)
        check = re.search(Config.CHANNEL_URL_REGEX, url)
        if check != None:
            return SearchMode(SearchMode.Types.CHANNEL), check.group(1)
        return SearchMode(SearchMode.Types.UNKNOWN), url