from Core.Config import Config as CoreConfig
from Services.Utils.OSUtils import OSUtils

_P = OSUtils.joinPath
_U = OSUtils.joinUrl

class Config:
    TRANSLATORS_PATH = _P(CoreConfig.UI_ROOT, "translators")
    TRANSLATIONS_PATH = _P(CoreConfig.RESOURCE_ROOT, "translations")

    LANGUAGES = {
        "en": {
            "name": "English",
            "preferredTimezone": "US/Eastern",
            "font": "Arial, Open Sans, 나눔고딕"
        },
        "ko": {
            "name": "한국어",
            "preferredTimezone": "Asia/Seoul",
            "font": "나눔고딕"
        }
    }

    TRANSLATION_LIST = [
        "mainWindow",
        "loading",
        "setup",
        "settings",
        "propertyView",
        "account",
        "about",
        "documentView",
        "home",
        "search",
        "videoWidget",
        "videoDownloadWidget",
        "searchResult",
        "downloadMenu",
        "downloads",
        "downloadPreview",
        "download"
    ]