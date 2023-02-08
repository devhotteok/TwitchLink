from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Services.Logging.ErrorDetector import ErrorDetector


class Updaters:
    @staticmethod
    def CleanUnknownVersion(data):
        try:
            OSUtils.removeDirectory(Config.TEMP_PATH)
        except:
            pass
        return {}

    @staticmethod
    def Update_2_0_0(data):
        data.pop("account", None)
        if "general" in data:
            generalData = data["general"]
            generalData.pop("_autoClose", None)
        data.pop("localization", None)
        data.pop("temp", None)
        data.pop("download", None)
        return data

    @staticmethod
    def Update_2_2_0(data):
        try:
            OSUtils.removeDirectory(OSUtils.joinPath(Config.APPDATA_PATH, "webdrivers"))
        except:
            pass
        data.pop("setup", None)
        data.pop("account", None)
        if "general" in data:
            generalData = data["general"]
            generalData["__type__"] = "obj:Database.Database:General"
        if "templates" in data:
            templatesData = data["templates"]
            templatesData["__type__"] = "obj:Database.Database:Templates"
        if "advanced" in data:
            advancedData = data["advanced"]
            advancedData["_searchExternalContent"] = advancedData.pop("_externalContentUrl")
            advancedData["__type__"] = "obj:Database.Database:Advanced"
        data.pop("localization", None)
        if "temp" in data:
            tempData = data["temp"]
            tempData["_downloadOptionHistory"] = data["temp"]["_downloadHistory"]
            tempData["_downloadHistory"] = []
            tempData["_downloadOptionHistory"]["stream"]["__type__"] = "obj:Download.DownloadOptionHistory:StreamHistory"
            tempData["_downloadOptionHistory"]["video"]["__type__"] = "obj:Download.DownloadOptionHistory:VideoHistory"
            tempData["_downloadOptionHistory"]["clip"]["__type__"] = "obj:Download.DownloadOptionHistory:ClipHistory"
            tempData["_downloadOptionHistory"]["image"]["__type__"] = "obj:Download.DownloadOptionHistory:ThumbnailHistory"
            tempData["_blockedContent"] = {"__type__": "dict"}
            tempData["__type__"] = "obj:Database.Database:Temp"
        if "download" in data:
            downloadData = data["download"]
            downloadData["__type__"] = "obj:Database.Database:Download"
        return data

    @staticmethod
    def Update_2_2_2(data):
        if "temp" in data:
            data["temp"].pop("_downloadHistory", None)
            data["temp"]["_downloadOptionHistory"]["stream"].pop("_optimizeFile", None)
        return data

    @staticmethod
    def Update_2_2_3(data):
        if "account" in data:
            if "_user" in data["account"]:
                data["account"]["_account"] = data["account"].pop("_user")
        if "temp" in data:
            data["temp"].pop("_downloadHistory", None)
            data["temp"]["_downloadOptionHistory"]["video"].pop("_optimizeFile", None)
        return data

    @staticmethod
    def Update_2_3_0(data):
        if "setup" in data:
            data["setup"]["_termsOfServiceAgreement"] = None
        if "temp" in data:
            data["temp"].pop("_downloadOptionHistory", None)
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
            "2.0.0": cls.Update_2_0_0,
            "2.0.1": None,
            "2.0.2": None,
            "2.1.0": None,
            "2.2.0": cls.Update_2_2_0,
            "2.2.1": None,
            "2.2.2": cls.Update_2_2_2,
            "2.2.3": cls.Update_2_2_3,
            "2.3.0": cls.Update_2_3_0,
            "2.3.1": None
        }
        updaters = []
        versionFound = False
        for key, value in VERSIONS.items():
            if versionFound:
                if value != None:
                    updaters.append(value)
            elif key == versionFrom:
                versionFound = True
        return updaters if versionFound else [cls.CleanUnknownVersion]

    @classmethod
    def update(cls, data):
        updaters = cls.getUpdaters(cls.detectVersion(data))
        if len(updaters) != 0:
            for updater in updaters:
                data = updater(data)
            ErrorDetector.clearAll()
        return data

    @classmethod
    def detectVersion(cls, data):
        try:
            return data.pop("version").split(":", 1)[1]
        except:
            return ""