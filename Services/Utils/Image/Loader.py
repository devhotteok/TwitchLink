from .Cache import ImageCache
from .Config import Config

from Core import GlobalExceptions

from PyQt5 import QtGui

import re


class Exceptions(GlobalExceptions.Exceptions):
    class NoPlaceholder(Exception):
        def __str__(self):
            return "Placeholder Not Provided"


class ImageLoader:
    IMAGE_SIZE_FORMAT = "-{width}x{height}"
    IMAGE_SIZE_FILTER = re.compile("-\d+x\d+")

    def __init__(self, target, url, placeholder=None, preferredSize=None, refresh=False):
        super().__init__()
        self.target = target
        self.url = url
        self.placeholder = placeholder
        self.size = preferredSize
        self.refresh = refresh
        self.loadImage()

    def setImage(self, pixmap):
        try:
            self.target.setPixmap(pixmap)
        except:
            pass

    def imageLoaded(self, pixmap):
        if pixmap == None:
            nextUrl = self.getNextUrl()
            if nextUrl != None:
                self.requestOnlineImage(nextUrl)
        else:
            self.setImage(pixmap)

    def isOnlineImage(self):
        return self.url.startswith("http://") or self.url.startswith("https://")

    def loadImage(self):
        if self.url == "":
            if self.placeholder == None:
                raise Exceptions.NoPlaceholder
            self.setImage(QtGui.QPixmap(self.placeholder))
        elif self.isOnlineImage():
            if self.placeholder == None:
                raise Exceptions.NoPlaceholder
            self.setImage(QtGui.QPixmap(self.placeholder))
            self.onlineUrls = list(self.generateResizedUrls())
            self.requestOnlineImage(self.getNextUrl())
        else:
            self.setImage(QtGui.QPixmap(self.url))

    def generateResizedUrls(self):
        if self.size == None:
            for serverUrl, size in Config.IMAGE_SIZE_POLICY:
                if self.url.startswith(serverUrl):
                    self.size = size
                    break
        cleanResizedUrl = self.appendSizeToUrl(re.sub(self.IMAGE_SIZE_FILTER, self.IMAGE_SIZE_FORMAT, self.url))
        resizedUrl = self.appendSizeToUrl(self.url)
        yield cleanResizedUrl
        if cleanResizedUrl != resizedUrl:
            yield resizedUrl

    def getNextUrl(self):
        return None if len(self.onlineUrls) == 0 else self.onlineUrls.pop(0)

    def requestOnlineImage(self, url):
        ImageCache.request(url, self.imageLoaded, refresh=self.refresh)

    def appendSizeToUrl(self, url):
        if self.size == None:
            return url.replace(self.IMAGE_SIZE_FORMAT, "")
        else:
            return url.format(width=self.size[0], height=self.size[1])