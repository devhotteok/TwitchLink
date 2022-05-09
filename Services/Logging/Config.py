from Core.Config import Config as CoreConfig

import logging


class Config:
    LOG_ROOT = CoreConfig.TEMP_PATH

    TARGET_ROOT = "root"
    TARGET_NOT_ROOT = "not_root"

    SECURITY_REPLACEMENTS = [
        "auth_token",
        "oauth_token"
    ]

    REPLACEMENT_STRING = "[---{appName} automatically replaced this({dataType}) for security reasons---]"

    STREAM_HANDLERS = [
        {
            "minLevel": logging.INFO,
            "maxLevel": logging.CRITICAL,
            "formatString": "[%(name)s] [%(levelname)s] %(message)s"
        }
    ]

    FILE_HANDLERS = [
        {
            "target": TARGET_NOT_ROOT,
            "minLevel": logging.DEBUG,
            "maxLevel": logging.DEBUG,
            "formatString": None
        },
        {
            "minLevel": logging.INFO,
            "maxLevel": logging.WARNING,
            "formatString": "[%(asctime)s][%(levelname)s] %(message)s"
        },
        {
            "minLevel": logging.ERROR,
            "maxLevel": logging.CRITICAL,
            "formatString": "[%(asctime)s][%(levelname)s][%(filename)s:%(lineno)s] %(message)s"
        }
    ]