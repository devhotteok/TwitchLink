from Core.Config import Config as CoreConfig, _P


class Config:
    DIRECTORY_PREFIX = "{}_".format(CoreConfig.APP_NAME)
    TEMP_LIST_DIRECTORY = _P(CoreConfig.APPDATA_PATH, "tempdirs")