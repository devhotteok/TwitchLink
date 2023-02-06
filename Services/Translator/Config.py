from Core.Config import Config as CoreConfig
from Services.Utils.OSUtils import OSUtils

from PyQt5 import QtCore


_P = OSUtils.joinPath
_U = OSUtils.joinUrl


class Config:
    TRANSLATORS_PATH = _P(CoreConfig.UI_ROOT, "translators")
    TRANSLATIONS_PATH = _P(CoreConfig.RESOURCE_ROOT, "translations")

    LANGUAGES = {
        "en": {
            "languageId": QtCore.QLocale.English,
            "name": "English",
            "font": "Arial, Open Sans, 나눔고딕"
        },
        "ko": {
            "languageId": QtCore.QLocale.Korean,
            "name": "한국어",
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
        "download",
        "scheduledDownloads",
        "scheduledDownloadPreview",
        "scheduledDownloadSettings",
        "downloadHistory",
        "downloadHistoryView",
        "webViewWidget"
    ]