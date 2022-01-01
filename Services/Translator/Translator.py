from .Config import Config

from Services.Utils.OSUtils import OSUtils

from PyQt5 import QtGui, QtCore

import json


class Exceptions:
    class LanguageNotFound(Exception):
        def __str__(self):
            return "Language Not Found"


class _Translator():
    def __init__(self):
        super().__init__()
        self.translators = []
        self.translations = {}
        for fileName in ["TwitchLinkKeywordTranslations.json", "TwitchLinkTranslations.json"]:
            try:
                with open("{}/{}".format(Config.TRANSLATIONS_PATH, fileName), encoding="utf-8") as file:
                    self.translations.update(json.load(file))
            except:
                pass
        self.setLanguage(self.getDefaultLanguage())

    def reload(self):
        if QtCore.QCoreApplication.instance() != None:
            self.unload()
            self.load()

    def load(self):
        language = self.getLanguage()
        path = QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath)
        for fileName in ["qtbase_{}"]:
            QtTranslator = QtCore.QTranslator()
            QtTranslator.load(fileName.format(language), path)
            self.translators.append(QtTranslator)
            QtCore.QCoreApplication.installTranslator(QtTranslator)
        path = OSUtils.joinPath(Config.TRANSLATORS_PATH, language)
        for translation in Config.TRANSLATION_LIST:
            UiTranslator = QtCore.QTranslator()
            UiTranslator.load(translation, path)
            self.translators.append(UiTranslator)
            QtCore.QCoreApplication.installTranslator(UiTranslator)

    def unload(self):
        for translator in self.translators:
            QtCore.QCoreApplication.removeTranslator(translator)
        self.translators = []

    def getLanguageData(self):
        return Config.LANGUAGES

    def getLanguageList(self):
        return [language["name"] for language in Config.LANGUAGES.values()]

    def getLanguageKeyList(self):
        return list(Config.LANGUAGES)

    def getDefaultLanguage(self):
        return self.getLanguageCode(0)

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
        font.setFamily(Config.LANGUAGES[self.getLanguage()]["font"]["default"])
        return font

    def getDocFont(self, font=QtGui.QFont()):
        font.setFamily(Config.LANGUAGES[self.getLanguage()]["font"]["doc"])
        return font

    def translate(self, string, noFormat=False, ellipsis=False, **kwargs):
        string = self.translateString(string)
        if noFormat == False:
            string = string.format(**kwargs)
        if ellipsis:
            return "{}...".format(string)
        else:
            return string

    def translateString(self, string):
        try:
            return self.translations[string][self.language]
        except:
            return string

Translator = _Translator()
T = Translator.translate