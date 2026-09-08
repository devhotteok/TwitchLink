from Services.Utils.OSUtils import OSUtils

from PyQt6 import QtCore

import os
import json


class JsonTranslator(QtCore.QTranslator):
    def __init__(self, translations: dict[str, str], parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._translations = translations

    def translate(self, context: str, sourceText: str, disambiguation: str | None = None, n: int = -1) -> str:
        if sourceText in self._translations:
            return self._translations[sourceText]
        return None


class TranslationPack(QtCore.QObject):
    def __init__(self, id: str, languageCode: str, displayName: str, staticTranslatorsPath: str, dynamicTranslationsPath: str, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._id = id
        self._languageCode = languageCode
        self._displayName = displayName
        self._staticTranslatorsPath = staticTranslatorsPath
        self._dynamicTranslationsPath = dynamicTranslationsPath

    def getId(self) -> str:
        return self._id

    def getLanguageCode(self) -> str:
        return self._languageCode

    def getDisplayName(self) -> str:
        return self._displayName

    def _loadStaticTranslator(self, fileName: str, directory: str) -> QtCore.QTranslator:
        translator = QtCore.QTranslator(parent=self)
        translator.load(fileName, directory)
        return translator

    def getStaticTranslators(self) -> list[QtCore.QTranslator]:
        translators = []
        directory = QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.TranslationsPath)
        for fileName in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, fileName)):
                if fileName.endswith(f"_{self._languageCode}.qm"):
                    translators.append(self._loadStaticTranslator(fileName, directory))
        translators.append(JsonTranslator(self.getDynamicTranslations(), parent=self))
        return translators

    def getDynamicTranslations(self) -> dict[str, str]:
        translations: dict[str, str] = {}
        fileName = f"{self._languageCode}.json"
        try:
            with open(OSUtils.joinPath(self._dynamicTranslationsPath, fileName), encoding="utf-8") as file:
                translations.update(json.load(file))
        except:
            pass
        return translations