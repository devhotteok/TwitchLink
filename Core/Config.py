from Core.Meta import Meta
from Services.Utils.OSUtils import OSUtils


_P = OSUtils.joinPath
_U = OSUtils.joinUrl


class Config(Meta):
    APP_ROOT = _P(OSUtils.getAppDirectory())

    SYSTEM_HOME_ROOT = _P(OSUtils.getSystemHomeRoot())

    RESOURCE_ROOT = _P(APP_ROOT, "resources")
    UI_ROOT = _P(RESOURCE_ROOT, "ui")
    DEPENDENCIES_ROOT = _P(RESOURCE_ROOT, "dependencies", OSUtils.getOSType().lower())
    DOCS_ROOT = _P(RESOURCE_ROOT, "docs")

    APPDATA_PATH = _P(OSUtils.getSystemAppDataPath(), Meta.APP_NAME)
    APPDATA_FILE = _P(APPDATA_PATH, "settings.json")
    TRACEBACK_FILE = _P(APPDATA_PATH, "traceback")

    TEMP_PATH = _P(OSUtils.getSystemTempPath(), Meta.APP_NAME)

    DEFAULT_DIRECTORY = _P(SYSTEM_HOME_ROOT, Meta.APP_NAME)

    SERVER_URL = _U(Meta.HOMEPAGE_URL, "server")

    CRASH_AUTOMATIC_RESTART_COOLDOWN = 60

    STATUS_UPDATE_INTERVAL = 60000
    STATUS_UPDATE_NETWORK_ERROR_MAX_IGNORE_COUNT = 1440
    STATUS_UPDATE_MAX_REDIRECT_COUNT = 10

    USER_AGENT_FORMAT = None

    SHOW_STATS = [50, [10, 30]]

    APP_SHUTDOWN_TIMEOUT = 60
    SYSTEM_SHUTDOWN_TIMEOUT = 100