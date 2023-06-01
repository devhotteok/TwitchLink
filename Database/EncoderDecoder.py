from PyQt6 import QtCore

import importlib


class Exceptions:
    class EncodeError(Exception):
        def __init__(self, obj):
            self.obj = obj

        def __str__(self):
            return f"Object Not Codable\ntype: {self.obj.__class__}\nobject: {self.obj}"

    class DecodeError(Exception):
        def __init__(self, objectType, objectData):
            self.objectType = objectType
            self.objectData = objectData

        def __str__(self):
            return f"Object Not Codable\ntype: {self.objectType}\nobjectData: {self.objectData}"

    class ModelCreateError(DecodeError):
        def __str__(self):
            return f"Model Create Error\ntype: {self.objectType}\nobjectData: {self.objectData}"

    class MissingRequiredDataError(DecodeError):
        def __str__(self):
            return f"Missing Required Data\ntype: {self.objectType}\nrequiredData: {self.objectType.CODABLE_REQUIRED_DATA}\nobjectData: {self.objectData}"

    class DataMismatchError(DecodeError):
        def __init__(self, objectType, mismatchKey, objectData, instanceData):
            super(Exceptions.DataMismatchError, self).__init__(objectType, objectData)
            self.mismatchKey = mismatchKey
            self.instanceData = instanceData

        def __str__(self):
            return f"Data Mismatch\ntype: {self.objectType}\nmismatchKey: {self.mismatchKey}\nobjectData: {self.objectData}\ninstanceData: {self.instanceData}"


class Codable:
    CODABLE_INIT_MODEL = True
    CODABLE_STRICT_MODE = True
    CODABLE_REQUIRED_DATA = []

    @classmethod
    def __model__(cls, data):
        if cls.CODABLE_INIT_MODEL:
            return cls()
        else:
            return cls.__new__(cls)

    def __update__(self, data):
        if self.CODABLE_STRICT_MODE:
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    raise Exceptions.DataMismatchError(self.__class__, key, data, self.__dict__)
        else:
            self.__dict__.update(data)

    def __setup__(self):
        pass

    @classmethod
    def __load__(cls, data):
        if not all(key in data.keys() for key in cls.CODABLE_REQUIRED_DATA):
            raise Exceptions.MissingRequiredDataError(cls, data)
        try:
            obj = cls.__model__(data)
        except:
            raise Exceptions.ModelCreateError(cls, data)
        obj.__update__(data)
        obj.__setup__()
        return obj

    def __save__(self):
        return self.__dict__


class Encoder:
    @classmethod
    def encode(cls, obj):
        if isinstance(obj, str):
            return f"str:{obj}"
        elif isinstance(obj, QtCore.QDateTime):
            return f"datetime:{obj.toString(QtCore.Qt.DateFormat.ISODateWithMs)}"
        elif isinstance(obj, QtCore.QTimeZone):
            return f"timezone:{obj.id().data().decode()}"
        elif isinstance(obj, bytes):
            return f"bytes:{obj.decode()}"
        elif isinstance(obj, bytearray):
            return f"bytearray:{obj.decode()}"
        elif isinstance(obj, tuple):
            return cls._encodeTuple(obj)
        elif isinstance(obj, list):
            return cls._encodeList(obj)
        elif isinstance(obj, dict):
            return cls._encodeDict(obj)
        elif cls._isObjectType(obj):
            return cls._encodeObject(obj)
        else:
            return obj

    @classmethod
    def _encodeTuple(cls, obj):
        return {"data": cls._encodeList(obj), "__type__": "tuple"}

    @classmethod
    def _encodeList(cls, obj):
        return [cls.encode(data) for data in obj]

    @classmethod
    def _encodeDict(cls, obj):
        data = {key: cls.encode(value) for key, value in obj.items()}
        data["__type__"] = "dict"
        return data

    @classmethod
    def _encodeObject(cls, obj):
        if isinstance(obj, Codable):
            data = {key: cls.encode(value) for key, value in obj.__save__().items()}
            data["__type__"] = f"obj:{obj.__class__.__module__}:{obj.__class__.__qualname__}"
        else:
            raise Exceptions.EncodeError(obj)
        return data

    @classmethod
    def _isObjectType(cls, obj):
        return hasattr(obj, "__dict__")


class Decoder:
    @classmethod
    def decode(cls, obj):
        if isinstance(obj, list):
            obj = cls._decodeList(obj)
        elif isinstance(obj, dict):
            obj = cls._decodeDict(obj)
        elif isinstance(obj, str):
            obj = cls._decodeString(obj)
        return obj

    @classmethod
    def _decodeList(cls, obj):
        return [cls.decode(data) for data in obj]

    @classmethod
    def _decodeDict(cls, obj):
        dataType = obj.pop("__type__", "dict")
        if dataType.startswith("obj:"):
            moduleInfo, classInfo = dataType.split(":", 1)[1].split(":", 1)
            objectType = importlib.import_module(moduleInfo)
            for name in classInfo.split("."):
                objectType = getattr(objectType, name)
            objectData = {key: cls.decode(value) for key, value in obj.items()}
            if issubclass(objectType, Codable):
                return objectType.__load__(objectData)
            else:
                raise Exceptions.DecodeError(objectType, objectData)
        elif dataType == "tuple":
            return tuple(cls.decode(data) for data in obj["data"])
        else:
            return {key: cls.decode(obj[key]) for key, value in obj.items()}

    @classmethod
    def _decodeString(cls, obj):
        key, data = obj.split(":", 1)
        if key == "str":
            return data
        elif key == "datetime":
            return QtCore.QDateTime.fromString(data, QtCore.Qt.DateFormat.ISODateWithMs)
        elif key == "timezone":
            return QtCore.QTimeZone(data.encode())
        elif key == "bytes":
            return data.encode()
        elif key == "bytearray":
            return bytearray(data.encode())
        else:
            return obj