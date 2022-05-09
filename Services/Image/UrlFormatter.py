from .Config import Config

import re


class ImageUrlFormatter:
    IMAGE_SIZE_FORMAT = "-{width}x{height}"
    IMAGE_SIZE_FILTER = re.compile("-\d+x\d+")

    @classmethod
    def formatUrl(cls, url, width=None, height=None):
        for host, size in Config.IMAGE_FORCED_SIZE_POLICY:
            if url.split("//", 1)[-1].startswith(host):
                width, height = size
                break
        if width == None or height == None:
            return re.sub(cls.IMAGE_SIZE_FILTER, "", url).replace(cls.IMAGE_SIZE_FORMAT, "")
        else:
            url = re.sub(cls.IMAGE_SIZE_FILTER, cls.IMAGE_SIZE_FORMAT, url)
            try:
                return url.format(width=width, height=height)
            except:
                return url