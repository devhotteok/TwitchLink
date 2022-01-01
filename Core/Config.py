from Core.Meta import Meta
from Services.Utils.OSUtils import OSUtils

import os
import sys


_P = OSUtils.joinPath
_U = OSUtils.joinUrl

class Config(Meta):
    APP_PATH = _P(sys.executable)
    APP_ROOT = _P(os.getcwd())
    SYSTEM_DRIVE = _P(os.getenv("SYSTEMDRIVE"))

    RESOURCE_ROOT = _P(APP_ROOT, "resources")
    UI_ROOT = _P(RESOURCE_ROOT, "ui")

    IMAGE_ROOT = _P(RESOURCE_ROOT, "img")
    DEPENDENCIES_ROOT = _P(RESOURCE_ROOT, "dependencies")
    DOCS_ROOT = _P(RESOURCE_ROOT, "docs")

    APPDATA_PATH = _P(os.getenv("APPDATA"), Meta.APP_NAME)

    DB_ROOT = APPDATA_PATH
    DB_FILE = _P(DB_ROOT, "settings.tl")

    LOG_ROOT = APPDATA_PATH
    DOWNLOAD_LOGS = _P(SYSTEM_DRIVE, Meta.APP_NAME, "logs.txt")

    ICON_IMAGE = _P(IMAGE_ROOT, "icon.ico")
    LOGO_IMAGE = _P(IMAGE_ROOT, "logo.png")
    LOGO_IMAGE_WHITE = _P(IMAGE_ROOT, "logo-white.png")
    OFFLINE_IMAGE = _P(IMAGE_ROOT, "channel_offline.png")
    PROFILE_IMAGE = _P(IMAGE_ROOT, "profile_image.png")
    PREVIEW_IMAGE = _P(IMAGE_ROOT, "preview.png")
    THUMBNAIL_IMAGE = _P(IMAGE_ROOT, "thumbnail.png")
    CATEGORY_IMAGE = _P(IMAGE_ROOT, "category.jpg")

    DEFAULT_FILE_DIRECTORY = _P(SYSTEM_DRIVE, Meta.APP_NAME)

    SERVER_URL = _U(Meta.HOMEPAGE_URL, "server")