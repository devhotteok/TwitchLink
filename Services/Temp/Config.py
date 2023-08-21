from Core.Config import Config as CoreConfig, _P


class Config:
    DIRECTORY_PREFIX = f".{CoreConfig.APP_NAME}_"
    TEMP_LIST_DIRECTORY = _P(CoreConfig.APPDATA_PATH, "tempdirs")
    TEMP_KEY_FILE_PREFIX = f"tmp_"
    DIRECTORY_LOCK_FILE_NAME = "Lock"