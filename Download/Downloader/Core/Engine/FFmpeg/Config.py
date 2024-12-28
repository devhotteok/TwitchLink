from Core.Config import Config as CoreConfig, _P
from Services.Utils.OSUtils import OSUtils


class Config:
    PATH = _P(CoreConfig.DEPENDENCIES_ROOT, f"ffmpeg{OSUtils.getExecutableType()}")

    KILL_TIMEOUT = 10000