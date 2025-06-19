from Services.Utils.OSUtils import OSUtils

from PyQt6 import QtCore

import os
import json


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
        directory = OSUtils.joinPath(self._staticTranslatorsPath, self._languageCode)
        if OSUtils.isDirectory(directory):
            for fileName in (data for data in OSUtils.listDirectory(directory) if OSUtils.isFile(OSUtils.joinPath(directory, data))):
                translators.append(self._loadStaticTranslator(fileName, directory))
        return translators

    def getDynamicTranslations(self) -> dict[str, str]:
        translations: dict[str, str] = {}
        for fileName in ["KeywordTranslations.json", "Translations.json"]:
            try:
                with open(OSUtils.joinPath(self._dynamicTranslationsPath, fileName), encoding="utf-8") as file:
                    translations.update({key: value.get(self._languageCode, key) for key, value in json.load(file).items()})
            except:
                pass
        return translations