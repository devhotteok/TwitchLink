from .Config import Config
from .TranslationPack import TranslationPack

from Core import App
from Services.Utils.SystemUtils import SystemUtils

from PyQt6 import QtCore


class Exceptions:
    class LanguageNotFound(Exception):
        def __str__(self):
            return "Language Not Found"


class Translator(QtCore.QObject):
    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._translationPacks: dict[str, TranslationPack] = {}
        self._currentTranslationPack: TranslationPack | None = None
        self._translationsCache: dict[str, str] = {}
        self._loadTranslations()
        self.setTranslationPack(self.getPreferredTranslationPackId())

    def _loadTranslations(self) -> None:
        for translationPackId, translationPackInfo in Config.LANGUAGES.items():
            translationPack = TranslationPack(
                id=translationPackId,
                languageCode=translationPackInfo["languageCode"],
                displayName=translationPackInfo["displayName"],
                staticTranslatorsPath=Config.TRANSLATORS_PATH,
                dynamicTranslationsPath=Config.TRANSLATIONS_PATH,
                parent=self
            )
            self._translationPacks[translationPack.getId()] = translationPack

    def setTranslationPack(self, translationPackId: str) -> None:
        if translationPackId not in self._translationPacks:
            raise Exceptions.LanguageNotFound
        if self._currentTranslationPack != None:
            for translator in self._currentTranslationPack.getStaticTranslators():
                App.Instance.removeTranslator(translator)
        self._currentTranslationPack = self._translationPacks[translationPackId]
        for translator in self._currentTranslationPack.getStaticTranslators():
            App.Instance.installTranslator(translator)
        self._translationsCache = self._currentTranslationPack.getDynamicTranslations()

    def getTranslationPacks(self) -> list[TranslationPack]:
        return list(self._translationPacks.values())

    def getPreferredLanguagePack(self) -> TranslationPack:
        systemLanguage = SystemUtils.getSystemLocale().language().name
        translationPacks = self.getTranslationPacks()
        for translationPack in translationPacks:
            if translationPack.getLanguageCode() == systemLanguage:
                return translationPack
        return translationPacks[0]

    def getPreferredTranslationPackId(self) -> str:
        return self.getPreferredLanguagePack().getId()

    def getCurrentTranslationPack(self) -> TranslationPack:
        return self._currentTranslationPack

    def getCurrentTranslationPackId(self) -> str:
        return self.getCurrentTranslationPack().getId()

    def getCurrentLanguageCode(self) -> str:
        return self._currentTranslationPack.getLanguageCode()

    def translate(self, string: str, ellipsis: bool = False, **kwargs: str) -> str:
        string = self._translationsCache.get(string, string)
        if kwargs:
            string = string.format(**kwargs)
        if ellipsis:
            return f"{string}..."
        else:
            return string