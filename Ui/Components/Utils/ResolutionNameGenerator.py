from Services.Translator.Translator import T


class ResolutionNameGenerator:
    @classmethod
    def generateResolutionName(cls, resolution):
        displayName = cls.removeBrackets(resolution.name)
        return T("audio-only") if resolution.isAudioOnly() else f"{displayName} ({T('source')})" if resolution.isSource() else displayName

    @classmethod
    def removeBrackets(self, string):
        newString = ""
        brackets = 0
        for char in string:
            if char == "(":
                brackets += 1
                continue
            elif char == ")":
                brackets -= 1
                continue
            if brackets == 0:
                newString += char
            elif brackets < 0:
                return string
        if brackets == 0:
            return " ".join(newString.split())
        else:
            return string