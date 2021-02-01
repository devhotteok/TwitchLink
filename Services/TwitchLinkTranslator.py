import json

from PyQt5.QtGui import QFont

from TwitchLinkConfig import Config


class LanguageNotFound(Exception):
    def __str__(self):
        return "\nLanguage Not Found"

class Translator:
    LANGUAGES = {"en": "English", "ko": "한국어"}
    FONTS = {"en": "Arial, Open Sans, 나눔고딕", "ko": "나눔고딕"}
    DOC_FONTS = {"en": "Arial, Open Sans", "ko": "Open Sans"}

    def __init__(self):
        self.translations = {}
        for fileName in ["TwitchLinkKeywordTranslations.json", "TwitchLinkTranslations.json"]:
            with open(Config.TRANSLATIONS_PATH + "/" + fileName, encoding="utf-8") as file:
                try:
                    self.translations.update(json.load(file))
                except:
                    pass
        self.setLanguage(list(Translator.LANGUAGES.keys())[0])

    def setLanguage(self, language):
        if language in self.LANGUAGES:
            self.language = language
        else:
            raise LanguageNotFound

    def getLanguage(self):
        return self.language

    def getFont(self, font=QFont()):
        font.setFamily(self.FONTS[self.getLanguage()])
        return font

    def getDocFont(self, font=QFont()):
        font.setFamily(self.DOC_FONTS[self.getLanguage()])
        return font

    def translate(self, string, **kwargs):
        if kwargs.get("noFormat") == True:
            return self.translateString(string)
        else:
            return self.translateString(string).format(**kwargs)

    def translateString(self, string):
        try:
            return self.translations[string][self.language]
        except:
            return string

translator = Translator()
T = translator.translate