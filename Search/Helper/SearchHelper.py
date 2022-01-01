from .Config import Config


class SearchHelper:
    @staticmethod
    def getChannelIdExamples():
        return Config.CHANNEL_ID_EXAMPLES

    @staticmethod
    def getVideoClipIdExamples():
        return Config.VIDEO_CLIP_ID_EXAMPLES

    @staticmethod
    def getUrlExamples():
        return Config.URL_EXAMPLES