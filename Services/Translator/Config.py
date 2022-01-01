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
            "font": {
                "default": "Arial, Open Sans, 나눔고딕",
                "doc": "Arial, Open Sans"
            }
        },
        "ko": {
            "name": "한국어",
            "preferredTimezone": "Asia/Seoul",
            "font": {
                "default": "나눔고딕",
                "doc": "Open Sans"
            }
        }
    }

    TRANSLATION_LIST = [
        "mainWindow",
        "loading",
        "settings",
        "formInfo",
        "account",
        "about",
        "termsOfService",
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