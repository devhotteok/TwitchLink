from Core.GlobalExceptions import Exceptions

import os
import platform
import shutil

from urllib.parse import urlencode

from PyQt6 import QtCore, QtGui


class OSUtils:
    isFile = os.path.isfile
    isDirectory = os.path.isdir
    removeFile = os.remove
    removeDirectory = shutil.rmtree
    openFolder = os.startfile
    openFile = os.startfile

    @staticmethod
    def openUrl(url):
        return QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    @staticmethod
    def copyToClipboard(text):
        QtGui.QGuiApplication.clipboard().setText(text)

    @staticmethod
    def joinPath(*args):
        return "/".join([string.strip("\\/") for string in args]).replace("\\", "/")

    @staticmethod
    def joinUrl(*args, params=None):
        url = "/".join([string.strip("/") for string in args])
        if params != None:
            return f"{url}?{urlencode(params)}"
        else:
            return url

    @staticmethod
    def createDirectory(directory):
        try:
            if not OSUtils.isDirectory(directory):
                os.makedirs(directory)
        except:
            raise Exceptions.FileSystemError

    @staticmethod
    def getValidFileName(name):
        characters = {
            "\\": "￦",
            "/": "／",
            ":": "：",
            "*": "＊",
            "?": "？",
            "\"": "＂",
            "<": "＜",
            ">": "＞",
            "|": "｜",
            "\n": "",
            "\r": "",
        }
        for key, value in characters.items():
            name = name.replace(key, value)
        return name.strip()

    @staticmethod
    def createUniqueFile(path, preferredFileName, fileFormat, exclude=None, maxScan=1000):
        exclude = exclude or []
        absoluteFileName = OSUtils.joinPath(path, f"{preferredFileName}.{fileFormat}")
        if absoluteFileName not in exclude:
            try:
                with open(absoluteFileName, "x"):
                    return absoluteFileName
            except:
                pass
        for i in range(maxScan):
            absoluteFileName = OSUtils.joinPath(path, f"{preferredFileName} ({i}).{fileFormat}")
            if absoluteFileName not in exclude:
                try:
                    with open(absoluteFileName, "x"):
                        return absoluteFileName
                except:
                    pass
        raise Exceptions.FileSystemError

    @staticmethod
    def getOSInfo():
        return f"{platform.system()} {platform.release()} {platform.version()}; {platform.machine()};"

    @staticmethod
    def shutdownSystem(message, time=10):
        os.system(f"shutdown /s /c \"{message}\" /t {time}")