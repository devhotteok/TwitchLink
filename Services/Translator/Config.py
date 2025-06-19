from Core.Config import Config as CoreConfig
from Services.Utils.OSUtils import OSUtils


_P = OSUtils.joinPath
_U = OSUtils.joinUrl


class Config:
    TRANSLATORS_PATH = _P(CoreConfig.UI_ROOT, "translators")
    TRANSLATIONS_PATH = _P(CoreConfig.RESOURCE_ROOT, "translations")

    LANGUAGES = {
        "en": {
            "languageId": "English",
            "languageCode": "en",
            "displayName": "English"
        },
        "ko": {
            "languageId": "Korean",
            "languageCode": "ko",
            "displayName": "한국어"
        }
    }