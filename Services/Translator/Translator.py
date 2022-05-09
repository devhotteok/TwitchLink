from .Config import Config

from Core.App import App
from Services.Utils.OSUtils import OSUtils
from Services.Utils.SystemUtils import SystemUtils

from PyQt5 import QtCore, QtGui

import json


class Exceptions:
    class LanguageNotFound(Exception):
        def __str__(self):
            return "Language Not Found"


class _Translator:
    def __init__(self, app):
        self.app = app
        self.translators = []
        self.translations = {}
        for fileName in ["KeywordTranslations.json", "Translations.json"]:
            try:
                with open(f"{Config.TRANSLATIONS_PATH}/{fileName}", encoding="utf-8") as file:
                    self.translations.update(json.load(file))
            except:
                pass
        self.setLanguage(self.getDefaultLanguage())

    def reload(self):
        self.unload()
        self.load()

    def load(self):
        language = self.getLanguage()
        directory = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath)
        for fileName in [f"qtbase_{language}"]:
            self._loadTranslator(fileName, directory)
        directory = OSUtils.joinPath(Config.TRANSLATORS_PATH, language)
        for fileName in Config.TRANSLATION_LIST:
            self._loadTranslator(fileName, directory)
        self.app.setFont(self.getFont())

    def _loadTranslator(self, fileName, directory):
        translator = QtCore.QTranslator(parent=self.app)
        translator.load(fileName, directory)
        self.translators.append(translator)
        self.app.installTranslator(translator)

    def unload(self):
        for translator in self.translators:
            self.app.removeTranslator(translator)
        self.translators = []

    def getLanguageData(self):
        return Config.LANGUAGES

    def getLanguageList(self):
        return [language["name"] for language in Config.LANGUAGES.values()]

    def getLanguageKeyList(self):
        return list(Config.LANGUAGES)

    def getDefaultLanguage(self):
        languageKeyList = self.getLanguageKeyList()
        systemLanguage = SystemUtils.getSystemLanguage().split("_")[0]
        if systemLanguage in languageKeyList:
            return systemLanguage
        else:
            return languageKeyList[0]

    def getLanguageCode(self, index):
        return self.getLanguageKeyList()[index]

    def setLanguage(self, language):
        if language in Config.LANGUAGES:
            self.language = language
            self.reload()
        else:
            raise Exceptions.LanguageNotFound

    def getLanguage(self):
        return self.language

    def getFont(self, font=QtGui.QFont()):
        font.setFamily(Config.LANGUAGES[self.getLanguage()]["font"])
        return font

    def translate(self, string, autoFormat=True, ellipsis=False, **kwargs):
        string = self.translateString(string)
        if autoFormat:
            string = string.format(**kwargs)
        if ellipsis:
            return f"{string}..."
        else:
            return string

    def translateString(self, string):
        try:
            return self.translations[string][self.language]
        except:
            return string

Translator = _Translator(app=App)
T = Translator.translate