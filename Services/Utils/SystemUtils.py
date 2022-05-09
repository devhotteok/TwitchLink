from Services.Threading.WorkerThread import WorkerThread

import locale
import pytz

from datetime import datetime


class SystemUtils:
    WorkerThread = WorkerThread

    @staticmethod
    def getSystemLanguage():
        return locale.getdefaultlocale()[0] or "en_US"

    @staticmethod
    def getTimezone(timezone):
        return pytz.timezone(timezone)

    @staticmethod
    def getTimezoneList():
        return list(pytz.common_timezones)

    @classmethod
    def getLocalTimezone(cls, preferred=None):
        timezoneList = cls.getLocalTimezoneList() or cls.getTimezoneList()
        if preferred in timezoneList:
            return cls.getTimezone(preferred)
        else:
            return cls.getTimezone(timezoneList[0])

    @classmethod
    def getLocalTimezoneList(cls):
        localUtcOffset = datetime.now() - datetime.utcnow()
        return [timezone for timezone in cls.getTimezoneList() if localUtcOffset == cls.getTimezone(timezone)]

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
                return f"{round(size, 2)}{sizeUnits[key]}"
        return size