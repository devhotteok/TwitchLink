from Core.Meta import Meta
from Services.Utils.OSUtils import OSUtils

import os


_P = OSUtils.joinPath
_U = OSUtils.joinUrl


class Config(Meta):
    APP_ROOT = _P(os.getcwd())

    SYSTEM_DRIVE = _P(os.getenv("SYSTEMDRIVE"))

    RESOURCE_ROOT = _P(APP_ROOT, "resources")
    UI_ROOT = _P(RESOURCE_ROOT, "ui")
    DEPENDENCIES_ROOT = _P(RESOURCE_ROOT, "dependencies")
    DOCS_ROOT = _P(RESOURCE_ROOT, "docs")

    APPDATA_PATH = _P(os.getenv("APPDATA"), Meta.APP_NAME)

    DB_ROOT = APPDATA_PATH
    DB_FILE = _P(DB_ROOT, "settings.tl")

    TEMP_PATH = _P(os.getenv("TEMP"), Meta.APP_NAME)

    DEFAULT_DIRECTORY = _P(SYSTEM_DRIVE, Meta.APP_NAME)

    SERVER_URL = _U(Meta.HOMEPAGE_URL, "server")

    STATUS_UPDATE_INTERVAL = 60000
    STATUS_UPDATE_NETWORK_ERROR_MAX_IGNORE_COUNT = 3

    APP_SHUTDOWN_TIMEOUT = 60
    SYSTEM_SHUTDOWN_TIMEOUT = 100