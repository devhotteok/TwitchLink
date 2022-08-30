from Core.Config import Config as CoreConfig

from PyQt5 import QtCore


class Config:
    PLAYLIST_FILE_NAME = CoreConfig.APP_NAME

    UPDATE_TRACK_MAX_RETRY_COUNT = 3
    UPDATE_TRACK_DURATION = 120
    SEGMENT_DOWNLOAD_MAX_RETRY_COUNT = 3

    MAX_THREAD_LIMIT = 20
    RECOMMENDED_THREAD_LIMIT = min(QtCore.QThread.idealThreadCount(), MAX_THREAD_LIMIT)