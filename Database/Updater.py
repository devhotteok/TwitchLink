from .EncoderDecoder import ObjectData

from Core.Config import Config
from Services.Utils.OSUtils import OSUtils

import os


class Updaters:
    @staticmethod
    def CleanUnknownVersion(data):
        try:
            OSUtils.removeDirectory(OSUtils.joinPath(os.getenv("TEMP"), Config.APP_NAME))
        except:
            pass
        return ObjectData()

    @staticmethod
    def Update_2_0_0(data):
        data = ObjectData(data)
        data["account"] = ObjectData(data["account"])
        data["account"]["_user"] = ObjectData(data["account"]["_user"])
        data["account"]["_user"]["data"] = None
        data["general"] = ObjectData(data["general"])
        data["templates"] = ObjectData(data["templates"])
        del data["localization"]
        del data["temp"]
        del data["download"]
        return data

    @classmethod
    def getUpdaters(cls, versionFrom):
        VERSIONS = {
            "1.0.0": None,
            "1.0.1": None,
            "1.0.2": None,
            "1.0.3": None,
            "1.0.4": None,
            "1.1.0": None,
            "1.1.1": None,
            "2.0.0": cls.Update_2_0_0
        }
        if versionFrom in VERSIONS:
            return list(VERSIONS.values())[list(VERSIONS.keys()).index(versionFrom) + 1:]
        else:
            return [cls.CleanUnknownVersion]