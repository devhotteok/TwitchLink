from Core.Config import Config
from Services.Utils.OSUtils import OSUtils

import typing


class Exceptions:
    class UnknownVersion(Exception):
        def __str__(self):
            return "Unknown Version"


class Updaters:
    @staticmethod
    def CleanUnknownVersion() -> None:
        try:
            OSUtils.removeDirectory(Config.TEMP_PATH)
        except:
            pass
        try:
            OSUtils.removeDirectory(Config.APPDATA_PATH)
        except:
            pass

    @classmethod
    def getUpdaters(cls, versionFrom: str) -> list[typing.Callable[[dict], dict]] | None:
        VERSIONS = {
            "3.0.0": None
        }
        updaters = []
        versionFound = False
        for key, value in VERSIONS.items():
            if versionFound:
                if value != None:
                    updaters.append(value)
            elif key == versionFrom:
                versionFound = True
        return updaters if versionFound else None

    @classmethod
    def update(cls, data: dict) -> dict:
        updaters = cls.getUpdaters(cls.detectVersion(data))
        if updaters == None:
            cls.CleanUnknownVersion()
            raise Exceptions.UnknownVersion
        else:
            for updater in updaters:
                data = updater(data)
            return data

    @classmethod
    def detectVersion(cls, data: dict) -> str:
        try:
            return data.pop("version").split(":", 1)[1]
        except:
            return ""