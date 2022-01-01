from Services.Utils.WorkerThreads import WorkerThread

import pytz

from datetime import datetime


class SystemUtils:
    WorkerThread = WorkerThread

    @staticmethod
    def hook(originalFunction, hookingFunction):
        return lambda *args, **kwargs: hookingFunction(lambda: originalFunction(*args, **kwargs))

    @staticmethod
    def getTimezone(timezone):
        return datetime.now(pytz.timezone(timezone)).utcoffset()

    @staticmethod
    def getTimezoneList():
        return list(pytz.common_timezones)

    @classmethod
    def getLocalTimezone(cls, preferredTimezones=None):
        timezoneList = cls.getLocalTimezoneList() or preferredTimezones or cls.getTimezoneList()
        for timezone in preferredTimezones or []:
            if timezone in timezoneList:
                return timezone
        return timezoneList[0]

    @classmethod
    def getLocalTimezoneList(cls):
        utcLocalOffset = datetime.now() - datetime.utcnow()
        return [timezone for timezone in cls.getTimezoneList() if utcLocalOffset == cls.getTimezone(timezone)]

    @staticmethod
    def formatByteSize(size):
        sizeUnits = {
            0: "B",
            1: "KB",
            2: "MB",
            3: "GB",
            4: "TB"
        }
        size = str(size).upper()
        for key in sizeUnits:
            check = size.strip(sizeUnits[key])
            if check.isnumeric():
                size = float(check)
                while size >= 1000:
                    if key == 4:
                        break
                    size /= 1024
                    key += 1
                return "{}{}".format(round(size, 2), sizeUnits[key])
        return size