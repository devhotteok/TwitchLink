from Core.Config import Config as CoreConfig, _P


class Config:
    DIRECTORY_PREFIX = f"{CoreConfig.APP_NAME}_"
    TEMP_LIST_DIRECTORY = _P(CoreConfig.APPDATA_PATH, "tempdirs")