from .Config import Config


class SearchHelper:
    @staticmethod
    def getChannelIdExamples() -> tuple[str, str]:
        return Config.CHANNEL_ID_EXAMPLES

    @staticmethod
    def getVideoIdExamples() -> tuple[str, str]:
        return Config.VIDEO_ID_EXAMPLES

    @staticmethod
    def getClipIdExamples() -> tuple[str, str]:
        return Config.CLIP_ID_EXAMPLES

    @staticmethod
    def getUrlExamples() -> tuple[str, str]:
        return Config.URL_EXAMPLES