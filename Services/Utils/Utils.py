from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Services.Utils.SystemUtils import SystemUtils
from Services.Utils.UiUtils import UiUtils
from Services.Translator.Translator import T


class Utils(OSUtils, SystemUtils, UiUtils):
    @staticmethod
    def injectionSafeFormat(string, **kwargs):
        index = 0
        while index < len(string):
            for key, value in kwargs.items():
                key = f"{{{key}}}"
                value = str(value)
                if string[index:].startswith(key):
                    string = f"{string[:index]}{value}{string[index + len(key):]}"
                    index += len(value) - 1
                    break
            index += 1
        return string

    @staticmethod
    def toSeconds(h, m, s):
        return int(h) * 3600 + int(m) * 60 + int(s)

    @staticmethod
    def toTime(seconds):
        seconds = int(seconds)
        return seconds // 3600, seconds % 3600 // 60, seconds % 3600 % 60

    @staticmethod
    def formatTime(h, m, s):
        return f"{h:02}:{m:02}:{s:02}"

    @staticmethod
    def getDoc(file, language, **kwargs):
        try:
            with open(Utils.joinPath(Config.DOCS_ROOT, language, file), "r", encoding="utf-8") as file:
                return T(file.read(), **kwargs)
        except:
            return ""