from .BaseAdapter import BaseAdapter

from Core.GlobalExceptions import Exceptions

import os
import sys
import platform
import shutil
import ctypes

from urllib.parse import urlencode

from PyQt6 import QtCore, QtGui, QtWidgets


class WindowsUtils(BaseAdapter):
    @staticmethod
    def getAppDirectory() -> str:
        return sys._MEIPASS if hasattr(sys, "_MEIPASS") else os.getcwd()

    @staticmethod
    def getSystemHomeRoot() -> str:
        return os.getenv("SYSTEMDRIVE")

    @staticmethod
    def getSystemAppDataPath() -> str:
        return os.getenv("APPDATA")

    @staticmethod
    def getSystemTempPath() -> str:
        return os.getenv("TEMP")

    @classmethod
    def getExecutableType(cls) -> str:
        return ".exe"

    @staticmethod
    def getLightStyle() -> QtWidgets.QStyle:
        return QtWidgets.QStyleFactory.create("windowsvista")

    @staticmethod
    def getDarkStyle() -> QtWidgets.QStyle:
        return QtWidgets.QStyleFactory.create("Fusion")

    @staticmethod
    def listDirectory(path: str) -> list[str]:
        return os.listdir(path)

    @staticmethod
    def isFile(path: str) -> bool:
        return os.path.isfile(path)

    @staticmethod
    def isDirectory(path: str) -> bool:
        return os.path.isdir(path)

    @staticmethod
    def removeFile(path: str) -> None:
        os.remove(path)

    @staticmethod
    def removeDirectory(path: str) -> None:
        shutil.rmtree(path)

    @staticmethod
    def renameFile(path: str, newPath: str) -> None:
        os.rename(path, newPath)

    @staticmethod
    def openFolder(path: str) -> bool:
        return QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))

    @staticmethod
    def openFile(path: str) -> bool:
        return QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(path))

    @staticmethod
    def openUrl(url) -> bool:
        return QtGui.QDesktopServices.openUrl(QtCore.QUrl(url))

    @staticmethod
    def copyToClipboard(text: str) -> None:
        QtGui.QGuiApplication.clipboard().setText(text)

    @staticmethod
    def joinPath(*args: str) -> str:
        return "/".join([value.rstrip("\\/") if index == 0 else value.strip("\\/") for index, value in enumerate(args)]).replace("\\", "/")

    @staticmethod
    def joinUrl(*args: str, params: dict[str, str] | None = None) -> str:
        url = "/".join([string.strip("/") for string in args])
        if params != None:
            return f"{url}?{urlencode(params)}"
        else:
            return url

    @classmethod
    def createDirectory(cls, directory: str) -> None:
        try:
            if not cls.isDirectory(directory):
                os.makedirs(directory)
        except:
            raise Exceptions.FileSystemError

    @staticmethod
    def getValidFileName(name: str) -> str:
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

    @classmethod
    def createUniqueFile(cls, path: str, preferredFileName: str, fileFormat: str, exclude: list[str] | None = None, maxScan: int = 1000) -> str:
        exclude = exclude or []
        absoluteFileName = cls.joinPath(path, f"{preferredFileName}.{fileFormat}")
        if absoluteFileName not in exclude:
            try:
                with open(absoluteFileName, "x"):
                    return absoluteFileName
            except:
                pass
        for index in range(maxScan):
            absoluteFileName = cls.joinPath(path, f"{preferredFileName} ({index}).{fileFormat}")
            if absoluteFileName not in exclude:
                try:
                    with open(absoluteFileName, "x"):
                        return absoluteFileName
                except:
                    pass
        raise Exceptions.FileSystemError

    @staticmethod
    def hideFileOrDirectory(target: str) -> None:
        ctypes.windll.kernel32.SetFileAttributesW(target, 2)

    @staticmethod
    def getOSInfo() -> str:
        return f"{platform.system()} {platform.release()} {platform.version()}; {platform.machine()}"

    @staticmethod
    def isMinimizeToSystemTraySupported() -> bool:
        return True

    @staticmethod
    def isSystemShutdownSupported() -> bool:
        return True

    @staticmethod
    def shutdownSystem(message: str, time: int = 10) -> None:
        os.system(f"shutdown /s /c \"{message}\" /t {time}")