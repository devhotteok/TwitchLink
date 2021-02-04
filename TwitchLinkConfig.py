import os
import sys


class Config:
    PROJECT_NAME = "TwitchLink"

    PROGRAM_PATH = sys.executable.replace("\\", "/")

    VERSION = "1.0.1"

    DB_COMPATIBLE_VERSIONS = ["1.0.0"]

    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__)).replace("\\", "/")
    SYSTEM_DRIVE = os.getenv("SYSTEMDRIVE").replace("\\", "/")

    RESOURCE_ROOT = PROJECT_ROOT + "/resources"
    UI_ROOT = RESOURCE_ROOT + "/ui"
    TRANSLATORS_PATH = UI_ROOT + "/translators"
    TRANSLATIONS_PATH = RESOURCE_ROOT + "/translations"
    IMAGE_ROOT = RESOURCE_ROOT + "/img"
    DEPENDENCIES_ROOT = RESOURCE_ROOT + "/dependencies"
    DOCS_ROOT = RESOURCE_ROOT + "/docs"

    APPDATA_PATH = os.getenv("APPDATA").replace("\\", "/") + "/" + PROJECT_NAME

    DB_ROOT = APPDATA_PATH
    DB_FILE = DB_ROOT + "/settings.tl"

    LOG_FILE = SYSTEM_DRIVE + "/" + PROJECT_NAME + "/logs.txt"

    ICON_IMAGE = IMAGE_ROOT + "/icon.ico"
    LOGO_IMAGE = IMAGE_ROOT + "/logo.png"
    OFFLINE_IMAGE = IMAGE_ROOT + "/offline_image.png"
    PROFILE_IMAGE = IMAGE_ROOT + "/profile_image.png"
    THUMBNAIL_IMAGE = IMAGE_ROOT + "/thumbnail.png"
    CATEGORY_IMAGE = IMAGE_ROOT + "/category.jpg"

    FILE_SAVE_DIRECTORY = SYSTEM_DRIVE + "/" + PROJECT_NAME
    TEMP_DIRECTORY = os.getenv("TEMP").replace("\\", "/") + "/" + PROJECT_NAME + "/vod"

    SERVER_URL = "https://twitchlink.github.io/server"
    HOMEPAGE_URL = "https://twitchlink.github.io"

    DATA_LOAD_LIMIT = 30

    AD_SERVER = None
    SHOW_ADS = True