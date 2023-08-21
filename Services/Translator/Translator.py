from .Config import Config

from Core import App
from Services.Utils.OSUtils import OSUtils
from Services.Utils.SystemUtils import SystemUtils

from PyQt6 import QtCore, QtGui

import os
import json


class Exceptions:
    class LanguageNotFound(Exception):
        def __str__(self):
            return "Language Not Found"


class Translator(QtCore.QObject):
    def __init__(self, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.translators = []
        self.translations = {}
        for fileName in ["KeywordTranslations.json", "Translations.json"]:
            try:
                with open(f"{Config.TRANSLATIONS_PATH}/{fileName}", encoding="utf-8") as file:
                    self.translations.update(json.load(file))
            except:
                pass
        self.setLanguage(self.getDefaultLanguage())

    def reload(self) -> None:
        self.unload()
        self.load()

    def load(self) -> None:
        language = self.getLanguage()
        directory = QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.TranslationsPath)
        for fileName in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, fileName)):
                if fileName.endswith(f"_{language}.qm"):
                    self._loadTranslator(fileName, directory)
        directory = OSUtils.joinPath(Config.TRANSLATORS_PATH, language)
        if OSUtils.isDirectory(directory):
            for fileName in (data for data in OSUtils.listDirectory(directory) if OSUtils.isFile(OSUtils.joinPath(directory, data))):
                self._loadTranslator(fileName, directory)
        App.Instance.setFont(self.getFont())

    def _loadTranslator(self, fileName: str, directory: str) -> None:
        translator = QtCore.QTranslator(parent=self)
        translator.load(fileName, directory)
        self.translators.append(translator)
        App.Instance.installTranslator(translator)

    def unload(self) -> None:
        for translator in self.translators:
            App.Instance.removeTranslator(translator)
        self.translators.clear()

    def getLanguageList(self) -> list[str]:
        return [language["name"] for language in Config.LANGUAGES.values()]

    def getLanguageKeyList(self) -> list[str]:
        return list(Config.LANGUAGES.keys())

    def getDefaultLanguage(self) -> str:
        systemLanguage = SystemUtils.getSystemLocale().language()
        for key, value in Config.LANGUAGES.items():
            if systemLanguage == value["languageId"]:
                return key
        return self.getLanguageCode(0)

    def getLanguageCode(self, index: int) -> str:
        return self.getLanguageKeyList()[index]

    def setLanguage(self, language: str) -> None:
        if language in Config.LANGUAGES:
            self.language = language
            self.reload()
        else:
            raise Exceptions.LanguageNotFound

    def getLanguage(self) -> str:
        return self.language

    def getFont(self, font: QtGui.QFont | None = None) -> QtGui.QFont:
        font = font or QtGui.QFont()
        font.setFamilies(Config.LANGUAGES[self.getLanguage()]["font"])
        return font

    def translate(self, string: str, ellipsis: bool = False, **kwargs: str) -> str:
        string = self.translateString(string)
        if kwargs:
            string = string.format(**kwargs)
        if ellipsis:
            return f"{string}..."
        else:
            return string

    def translateString(self, string: str) -> str:
        try:
            return self.translations[string][self.language]
        except:
            return string