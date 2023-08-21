from PyQt6 import QtCore


class SystemUtils:
    @staticmethod
    def getSystemLocale() -> QtCore.QLocale:
        return QtCore.QLocale.system()

    @staticmethod
    def getTimezone(timezoneId: bytes | QtCore.QByteArray) -> QtCore.QTimeZone:
        return QtCore.QTimeZone(timezoneId)

    @classmethod
    def getTimezoneNameList(cls) -> list[str]:
        return [cls.getTimezone(timezoneId).name() for timezoneId in QtCore.QTimeZone.availableTimeZoneIds()]

    @classmethod
    def getLocalTimezone(cls) -> QtCore.QTimeZone:
        return cls.getTimezone(QtCore.QTimeZone.systemTimeZoneId())