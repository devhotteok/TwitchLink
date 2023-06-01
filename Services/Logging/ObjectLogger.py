from .Config import Config

from Core.Config import Config as CoreConfig

from PyQt6 import QtCore

import json


class ObjectLogger:
    @classmethod
    def generateObjectLog(cls, target):
        return json.dumps(cls.getObjectData(target), indent=3, ensure_ascii=False)

    @classmethod
    def getObjectData(cls, target):
        if isinstance(target, dict):
            return {key: Config.REPLACEMENT_STRING.format(appName=CoreConfig.APP_NAME, dataType=key.lower()) if key.lower() in Config.SECURITY_REPLACEMENTS else cls.getObjectData(value) for key, value in target.items()}
        elif isinstance(target, list):
            return [cls.getObjectData(data) for data in target]
        elif isinstance(target, QtCore.QDateTime):
            return target.toString(QtCore.Qt.DateFormat.ISODateWithMs)
        elif hasattr(target, "__dict__"):
            return cls.getObjectData(target.__dict__)
        else:
            return target