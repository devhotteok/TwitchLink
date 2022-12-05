from Services.Translator.Translator import T


class ResolutionNameGenerator:
    @classmethod
    def generateResolutionName(cls, resolution):
        displayName = resolution.displayName
        return T("audio-only") if resolution.isAudioOnly() else f"{displayName} ({T('source')})" if resolution.isSource() else displayName