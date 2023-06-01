from Services.Threading.WorkerThread import WorkerThread

from PyQt6 import QtCore


class SystemUtils:
    WorkerThread = WorkerThread

    @staticmethod
    def getSystemLocale():
        return QtCore.QLocale.system()

    @staticmethod
    def getTimezone(timezoneId):
        return QtCore.QTimeZone(timezoneId)

    @classmethod
    def getTimezoneNameList(cls):
        return [cls.getTimezone(timezoneId).name() for timezoneId in QtCore.QTimeZone.availableTimeZoneIds()]

    @classmethod
    def getLocalTimezone(cls):
        return cls.getTimezone(QtCore.QTimeZone.systemTimeZoneId())

    @staticmethod
    def getByteSize(size):
        sizeUnits = {
            0: "B",
            1: "KB",
            2: "MB",
            3: "GB",
            4: "TB"
        }
        size = str(size).upper()
        for key, value in sizeUnits.items():
            check = size.strip(value)
            try:
                byteSize = float(check)
                break
            except:
                continue
        else:
            byteSize = 0
        for _ in range(key):
            byteSize *= 1024
        return int(byteSize)

    @staticmethod
    def formatByteSize(byteSize):
        sizeUnits = {
            0: "B",
            1: "KB",
            2: "MB",
            3: "GB",
            4: "TB"
        }
        for key in sizeUnits:
            if byteSize < 1000:
                break
            else:
                byteSize /= 1024
        return f"{round(byteSize, 2)}{sizeUnits[key]}"