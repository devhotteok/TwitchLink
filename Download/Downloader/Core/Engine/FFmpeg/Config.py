from Core.Config import Config as CoreConfig, _P


class Config:
    PATH = _P(CoreConfig.DEPENDENCIES_ROOT, "ffmpeg.exe")

    KILL_TIMEOUT = 10000