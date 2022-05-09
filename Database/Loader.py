from .Updater import Updaters
from .EncoderDecoder import ObjectData


class Exceptions:
    class TypeMismatch(Exception):
        def __str__(self):
            return "Type Mismatch Error"


class DataLoader:
    @classmethod
    def load(cls, database, data):
        for updater in Updaters.getUpdaters(cls.detectVersion(data)):
            data = updater(data)
        cls.unpack(database, data)

    @classmethod
    def detectVersion(cls, data):
        try:
            return data.pop("version")
        except:
            return ""

    @classmethod
    def unpack(cls, dataObject, data):
        if isinstance(data, ObjectData):
            if hasattr(dataObject, "__dict__"):
                return cls._unpackObject(dataObject, data)
            else:
                raise Exceptions.TypeMismatch
        elif isinstance(data, dict):
            if isinstance(dataObject, dict):
                return cls._unpackDict(dataObject, data)
            else:
                raise Exceptions.TypeMismatch
        else:
            return data

    @classmethod
    def _unpackDict(cls, dataObject, data):
        newDict = {}
        for key, value in data.items():
            if key in dataObject:
                newDict[key] = cls.unpack(dataObject[key], value)
            else:
                try:
                    cls._checkPureData(value)
                except:
                    raise Exceptions.TypeMismatch
                else:
                    newDict[key] = value
        return newDict

    @classmethod
    def _unpackObject(cls, dataObject, data):
        for key, value in data.items():
            if hasattr(dataObject, key):
                setattr(dataObject, key, cls.unpack(getattr(dataObject, key), value))
        return dataObject

    @classmethod
    def _checkPureData(cls, data):
        if isinstance(data, ObjectData):
            raise
        elif isinstance(data, dict):
            for value in data.values():
                cls._checkPureData(value)
        elif isinstance(data, list):
            for item in data:
                cls._checkPureData(item)