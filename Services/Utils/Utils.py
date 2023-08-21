from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Services.Utils.SystemUtils import SystemUtils
from Services.Utils.UiUtils import UiUtils


class Utils(OSUtils, SystemUtils, UiUtils):
    @staticmethod
    def injectionSafeFormat(string: str, **kwargs: str) -> str:
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
    def formatByteSize(byteSize: int) -> str:
        sizeUnits = {
            0: "B",
            1: "KB",
            2: "MB",
            3: "GB",
            4: "TB"
        }
        for key in sizeUnits:
            if byteSize < 1000:
                break
            else:
                byteSize /= 1024
        return f"{round(byteSize, 2):.2f}{sizeUnits[key]}"

    @staticmethod
    def formatMilliseconds(milliseconds: int) -> str:
        seconds = int(milliseconds / 1000)
        return f"{seconds // 3600:02}:{seconds % 3600 // 60:02}:{seconds % 3600 % 60:02}"

    @staticmethod
    def getDocument(file: str, language: str) -> str:
        try:
            with open(Utils.joinPath(Config.DOCS_ROOT, language, file), "r", encoding="utf-8") as file:
                return file.read()
        except:
            return ""