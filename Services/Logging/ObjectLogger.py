from .Config import Config

from Core.Config import Config as CoreConfig

import datetime
import json


class ObjectLogger:
    @classmethod
    def generateObjectLog(cls, target):
        return json.dumps(cls.getObjectData(target), indent=3, ensure_ascii=False)

    @classmethod
    def getObjectData(cls, target):
        if hasattr(target, "__dict__"):
            return cls.getObjectData(target.__dict__)
        elif isinstance(target, dict):
            data = {}
            for key in target:
                if key.lower() in Config.SECURITY_REPLACEMENTS:
                    data[key] = Config.REPLACEMENT_STRING.format(appName=CoreConfig.APP_NAME, dataType=key.lower())
                else:
                    data[key] = cls.getObjectData(target[key])
            return data
        elif isinstance(target, list):
            data = []
            for value in target:
                data.append(cls.getObjectData(value))
            return data
        elif isinstance(target, datetime.datetime) or isinstance(target, datetime.timedelta):
            return cls.getObjectData(str(target))
        else:
            return target