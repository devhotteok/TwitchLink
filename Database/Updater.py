from Core.Config import Config
from Services.Utils.OSUtils import OSUtils

import os


class Converters:
    @staticmethod
    def CleanUnknownVersion(data):
        try:
            OSUtils.removeDirectory(OSUtils.joinPath(os.getenv("TEMP"), Config.APP_NAME))
        except:
            pass
        return data

    @classmethod
    def getConverters(cls, versionFrom):
        VERSIONS = {
            "1.0.0": None,
            "1.0.1": None,
            "1.0.2": None,
            "1.0.3": None,
            "1.0.4": None,
            "1.1.0": None,
            "1.1.1": None
        }
        if versionFrom in VERSIONS:
            return list(VERSIONS.values())[list(VERSIONS.keys()).index(versionFrom) + 1:]
        else:
            return [cls.CleanUnknownVersion]