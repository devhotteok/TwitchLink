from Core.Config import Config
from Services.Utils.OSUtils import OSUtils

import typing


class Exceptions:
    class UnknownVersion(Exception):
        def __str__(self):
            return "Unknown Version"


class Updaters:
    @staticmethod
    def FindPreferences() -> None:
        if OSUtils.isFile(OSUtils.joinPath(Config.APPDATA_PATH, "settings.tl")):
            try:
                OSUtils.renameFile(OSUtils.joinPath(Config.APPDATA_PATH, "settings.tl"), Config.APPDATA_FILE)
            except:
                pass

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

    @staticmethod
    def Update_3_0_0(data: dict) -> dict:
        return {
            "setup": {
                "_needSetup": data["setup"]["_needSetup"],
                "_termsOfServiceAgreement": data["setup"]["_termsOfServiceAgreement"],
                "__type__": "obj:AppData.Preferences:Setup"
            },
            "account": {
                "_accountData": {
                    "data": [
                        None,
                        None
                    ] if data["account"]["_account"]["data"] == None else [
                        {
                            "id": f"str:{data['account']['_account']['data']['id']}",
                            "login": data["account"]["_account"]["data"]["login"],
                            "displayName": data["account"]["_account"]["data"]["displayName"],
                            "profileImageURL": data["account"]["_account"]["data"]["profileImageURL"],
                            "createdAt": data["account"]["_account"]["data"]["createdAt"],
                            "__type__": "obj:Services.Twitch.GQL.TwitchGQLModels:User"
                        },
                        {
                            "value": data["account"]["_account"]["token"],
                            "expiration": data["account"]["_account"]["expiry"],
                            "__type__": "obj:Services.Twitch.Authentication.OAuth.OAuthToken:OAuthToken"
                        }
                    ],
                    "__type__": "tuple"
                },
                "__type__": "obj:AppData.Preferences:Account"
            },
            "general": {
                "_openProgressWindow": data["general"]["_openProgressWindow"],
                "_notify": data["general"]["_notify"],
                "_useSystemTray": data["general"]["_useSystemTray"],
                "_bookmarks": data["general"]["_bookmarks"],
                "__type__": "obj:AppData.Preferences:General"
            },
            "templates": {
                "_streamFilename": data["templates"]["_streamFilename"],
                "_videoFilename": data["templates"]["_videoFilename"],
                "_clipFilename": data["templates"]["_clipFilename"],
                "__type__": "obj:AppData.Preferences:Templates"
            },
            "advanced": {
                "_searchExternalContent": data["advanced"]["_searchExternalContent"],
                "__type__": "obj:AppData.Preferences:Advanced"
            },
            "localization": {
                "_timezone": data["localization"]["_timezone"],
                "_language": data["localization"]["_language"],
                "__type__": "obj:AppData.Preferences:Localization"
            },
            "temp": {
                "__type__": "obj:AppData.Preferences:Temp"
            },
            "download": {
                "_downloadSpeed": data["download"]["_downloadSpeed"],
                "__type__": "obj:AppData.Preferences:Download"
            },
            "scheduledDownloads": {
                "_enabled": data["scheduledDownloads"]["_enabled"],
                "_scheduledDownloadPresets": [
                    {
                        "channel": preset["channel"],
                        "filenameTemplate": preset["filenameTemplate"],
                        "directory": preset["directory"],
                        "preferredQualityIndex": preset["preferredQualityIndex"],
                        "preferredFrameRateIndex": preset["preferredFrameRateIndex"],
                        "fileFormat": preset["fileFormat"],
                        "remux": True,
                        "preferredResolutionOnly": preset["preferredResolutionOnly"],
                        "enabled": preset["enabled"],
                        "__type__": "obj:Download.ScheduledDownloadPreset:ScheduledDownloadPreset"
                    } for preset in data["scheduledDownloads"]["_scheduledDownloadPresets"]
                ],
                "__type__": "obj:AppData.Preferences:ScheduledDownloads"
            },
            "__type__": "dict"
        }

    @staticmethod
    def Update_3_1_0(data: dict) -> dict:
        data["temp"] = {
            "__type__": "obj:AppData.Preferences:Temp"
        }
        data["scheduledDownloads"] = {
            "_enabled": data["scheduledDownloads"]["_enabled"],
            "_scheduledDownloadPresets": [
                {
                    "channel": preset["channel"],
                    "filenameTemplate": preset["filenameTemplate"],
                    "directory": preset["directory"],
                    "preferredQualityIndex": preset["preferredQualityIndex"],
                    "preferredFrameRateIndex": preset["preferredFrameRateIndex"],
                    "fileFormat": preset["fileFormat"],
                    "skipAds": True,
                    "remux": preset["remux"],
                    "preferredResolutionOnly": preset["preferredResolutionOnly"],
                    "enabled": preset["enabled"],
                    "__type__": "obj:Download.ScheduledDownloadPreset:ScheduledDownloadPreset"
                } for preset in data["scheduledDownloads"]["_scheduledDownloadPresets"]
            ],
            "__type__": "obj:AppData.Preferences:ScheduledDownloads"
        }
        return data

    @staticmethod
    def Update_3_2_0(data: dict) -> dict:
        data["advanced"]["_themeMode"] = "str:"
        return data

    @staticmethod
    def Update_3_3_0(data: dict) -> dict:
        data["temp"]["_downloadHistory"] = []
        return data

    @staticmethod
    def Update_3_5_0(data: dict) -> dict:
        languageCode = data.get("localization", {}).pop("_language", None)
        if languageCode != None:
            data["localization"]["_translationPackId"] = languageCode
        return data

    @classmethod
    def getUpdaters(cls, versionFrom: str) -> list[typing.Callable[[dict], dict]] | None:
        VERSIONS = {
            "2.3.2": None,
            "2.4.0": None,
            "3.0.0": cls.Update_3_0_0,
            "3.0.1": None,
            "3.0.2": None,
            "3.0.3": None,
            "3.0.4": None,
            "3.1.0": cls.Update_3_1_0,
            "3.1.1": None,
            "3.1.2": None,
            "3.1.3": None,
            "3.2.0": cls.Update_3_2_0,
            "3.2.1": None,
            "3.3.0": cls.Update_3_3_0,
            "3.4.0": None,
            "3.5.0": cls.Update_3_5_0,
            "3.5.1": None
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