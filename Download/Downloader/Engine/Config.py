from Core.Config import Config as CoreConfig


class Config:
    PLAYLIST_FILE_NAME = CoreConfig.APP_NAME

    UPDATE_TRACK_DURATION = 300
    SEGMENT_DOWNLOAD_MAX_RETRY_COUNT = 3
    SKIP_DOWNLOAD_ENABLE_POINT = 90