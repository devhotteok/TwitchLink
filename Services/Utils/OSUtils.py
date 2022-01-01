import os
import shutil

from urllib.parse import urlencode

from PyQt5 import QtCore, QtGui


class OSUtils:
    isFile = os.path.isfile
    isDirectory = os.path.isdir
    removeFile = os.remove
    removeDirectory = shutil.rmtree
    openFolder = os.startfile
    openFile = os.startfile

    @staticmethod
    def openUrl(url):
        QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    @staticmethod
    def copyToClipboard(text):
        QtGui.QGuiApplication.clipboard().setText(text)

    @staticmethod
    def joinPath(*args):
        return "/".join(map(lambda string: string.strip("\\/"), args)).replace("\\", "/")

    @staticmethod
    def joinUrl(*args, params=None):
        url = "/".join(map(lambda string: string.strip("/"), args))
        if params != None:
            return "{}?{}".format(url, urlencode(params))
        else:
            return url

    @staticmethod
    def createDirectory(directory):
        if not OSUtils.isDirectory(directory):
            os.makedirs(directory)

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