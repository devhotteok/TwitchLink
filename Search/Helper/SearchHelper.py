from .Config import Config


class SearchHelper:
    @staticmethod
    def getChannelIdExamples():
        return Config.CHANNEL_ID_EXAMPLES

    @staticmethod
    def getVideoIdExamples():
        return Config.VIDEO_ID_EXAMPLES

    @staticmethod
    def getClipIdExamples():
        return Config.CLIP_ID_EXAMPLES

    @staticmethod
    def getUrlExamples():
        return Config.URL_EXAMPLES