import abc
import platform

from PyQt6 import QtWidgets


class BaseAdapter(abc.ABC):
    @staticmethod
    def getOSType() -> str:
        system = platform.system()
        if system == "Windows":
            return "Windows"
        elif system == "Darwin":
            return "macOS"
        return ""

    @classmethod
    def isWindows(cls) -> bool:
        return cls.getOSType() == "Windows"

    @classmethod
    def isMacOS(cls) -> bool:
        return cls.getOSType() == "macOS"

    @staticmethod
    @abc.abstractmethod
    def getAppDirectory() -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    def getSystemHomeRoot() -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    def getSystemAppDataPath() -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    def getSystemTempPath() -> str:
        pass

    @classmethod
    def getExecutableType(cls) -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    def getLightStyle() -> QtWidgets.QStyle:
        pass

    @staticmethod
    @abc.abstractmethod
    def getDarkStyle() -> QtWidgets.QStyle:
        pass

    @staticmethod
    @abc.abstractmethod
    def listDirectory(path: str) -> list[str]:
        pass

    @staticmethod
    @abc.abstractmethod
    def isFile(path: str) -> bool:
        pass

    @staticmethod
    @abc.abstractmethod
    def isDirectory(path: str) -> bool:
        pass

    @staticmethod
    @abc.abstractmethod
    def removeFile(path: str) -> None:
        pass

    @staticmethod
    @abc.abstractmethod
    def removeDirectory(path: str) -> None:
        pass

    @staticmethod
    @abc.abstractmethod
    def renameFile(path: str, newPath: str) -> None:
        pass

    @staticmethod
    @abc.abstractmethod
    def openFolder(path: str) -> bool:
        pass

    @staticmethod
    @abc.abstractmethod
    def openFile(path: str) -> bool:
        pass

    @staticmethod
    @abc.abstractmethod
    def openUrl(url) -> bool:
        pass

    @staticmethod
    @abc.abstractmethod
    def copyToClipboard(text: str) -> None:
        pass

    @staticmethod
    @abc.abstractmethod
    def joinPath(*args: str) -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    def joinUrl(*args: str, params: dict[str, str] | None = None) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def createDirectory(cls, directory: str) -> None:
        pass

    @staticmethod
    @abc.abstractmethod
    def getValidFileName(name: str) -> str:
        pass

    @classmethod
    @abc.abstractmethod
    def createUniqueFile(cls, path: str, preferredFileName: str, fileFormat: str, exclude: list[str] | None = None, maxScan: int = 1000) -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    def hideFileOrDirectory(target: str) -> None:
        pass

    @staticmethod
    @abc.abstractmethod
    def getOSInfo() -> str:
        pass

    @staticmethod
    @abc.abstractmethod
    def isSystemShutdownSupported() -> bool:
        pass

    @staticmethod
    @abc.abstractmethod
    def shutdownSystem(message: str, time: int = 10) -> None:
        pass