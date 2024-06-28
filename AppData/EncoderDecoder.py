from PyQt6 import QtCore

import typing
import types
import importlib


class Exceptions:
    class EncodeError(Exception):
        def __init__(self, object: typing.Any):
            self.object = object

        def __str__(self):
            return f"Object Not Serializable\nType: {self.object.__class__}\nObject: {self.object}"

    class DecodeError(Exception):
        def __init__(self, objectType: types.ModuleType | typing.Type[typing.Any], objectData: dict):
            self.objectType = objectType
            self.objectData = objectData

        def __str__(self):
            return f"Object Not Serializable\nType: {self.objectType}\nObjectData: {self.objectData}"

    class ModelCreateError(DecodeError):
        def __str__(self):
            return f"Model Create Error\nType: {self.objectType}\nObjectData: {self.objectData}"

    class DataMismatchError(DecodeError):
        def __init__(self, objectType: typing.Type[typing.Any], mismatchKey: str, objectData: dict, instanceData: dict):
            super().__init__(objectType, objectData)
            self.mismatchKey = mismatchKey
            self.instanceData = instanceData

        def __str__(self):
            return f"Data Mismatch\nType: {self.objectType}\nMismatchKey: {self.mismatchKey}\nObjectData: {self.objectData}\nInstanceData: {self.instanceData}"


class Serializable:
    SERIALIZABLE_INIT_MODEL = True
    SERIALIZABLE_STRICT_MODE = True

    @classmethod
    def __model__(cls, data: dict) -> typing.Any:
        if cls.SERIALIZABLE_INIT_MODEL:
            return cls()
        else:
            return cls.__new__(cls)

    def __update__(self, data: dict) -> None:
        if self.SERIALIZABLE_STRICT_MODE:
            for key, value in data.items():
                if hasattr(self, key):
                    setattr(self, key, value)
                else:
                    raise Exceptions.DataMismatchError(self.__class__, key, data, self.__dict__)
        else:
            self.__dict__.update(data)

    def __setup__(self) -> None:
        pass

    @classmethod
    def __load__(cls, data: dict) -> typing.Any:
        try:
            obj = cls.__model__(data)
        except:
            raise Exceptions.ModelCreateError(cls, data)
        obj.__update__(data)
        obj.__setup__()
        return obj

    def __save__(self) -> dict:
        return self.__dict__

    def copy(self) -> typing.Self:
        return Decoder.decode(Encoder.encode(self))


class Encoder:
    @classmethod
    def encode(cls, obj: typing.Any) -> typing.Any:
        if isinstance(obj, str):
            return f"str:{obj}"
        elif isinstance(obj, QtCore.QDateTime):
            return f"datetime:{obj.toString(QtCore.Qt.DateFormat.ISODateWithMs)}"
        elif isinstance(obj, QtCore.QTimeZone):
            return f"timezone:{obj.id().data().decode(errors='ignore')}"
        elif isinstance(obj, QtCore.QUrl):
            return f"url:{obj.toString()}"
        elif isinstance(obj, bytes):
            return f"bytes:{obj.decode(errors='ignore')}"
        elif isinstance(obj, bytearray):
            return f"bytearray:{obj.decode(errors='ignore')}"
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
    def _encodeTuple(cls, obj: tuple) -> dict:
        return {"data": cls._encodeList(obj), "__type__": "tuple"}

    @classmethod
    def _encodeList(cls, obj: tuple | list) -> list:
        return [cls.encode(data) for data in obj]

    @classmethod
    def _encodeDict(cls, obj: dict) -> dict:
        data = {key: cls.encode(value) for key, value in obj.items()}
        data["__type__"] = "dict"
        return data

    @classmethod
    def _encodeObject(cls, obj: typing.Any) -> dict:
        if isinstance(obj, Serializable):
            data = {key: cls.encode(value) for key, value in obj.__save__().items()}
            data["__type__"] = f"obj:{obj.__class__.__module__}:{obj.__class__.__qualname__}"
        else:
            raise Exceptions.EncodeError(obj)
        return data

    @classmethod
    def _isObjectType(cls, obj: typing.Any) -> bool:
        return hasattr(obj, "__dict__")


class Decoder:
    @classmethod
    def decode(cls, obj: typing.Any) -> typing.Any:
        if isinstance(obj, list):
            obj = cls._decodeList(obj)
        elif isinstance(obj, dict):
            obj = cls._decodeDict(obj)
        elif isinstance(obj, str):
            obj = cls._decodeString(obj)
        return obj

    @classmethod
    def _decodeList(cls, obj: list) -> list:
        return [cls.decode(data) for data in obj]

    @classmethod
    def _decodeDict(cls, obj: dict) -> typing.Any:
        dataType = obj.pop("__type__", "dict")
        if dataType.startswith("obj:"):
            moduleInfo, classInfo = dataType.split(":", 1)[1].split(":", 1)
            objectType = importlib.import_module(moduleInfo)
            for name in classInfo.split("."):
                objectType = getattr(objectType, name)
            objectData = {key: cls.decode(value) for key, value in obj.items()}
            if issubclass(objectType, Serializable):
                return objectType.__load__(objectData)
            else:
                raise Exceptions.DecodeError(objectType, objectData)
        elif dataType == "tuple":
            return tuple(cls.decode(data) for data in obj["data"])
        else:
            return {key: cls.decode(obj[key]) for key, value in obj.items()}

    @classmethod
    def _decodeString(cls, obj: str) -> typing.Any:
        key, data = obj.split(":", 1)
        if key == "str":
            return data
        elif key == "datetime":
            return QtCore.QDateTime.fromString(data, QtCore.Qt.DateFormat.ISODateWithMs)
        elif key == "timezone":
            return QtCore.QTimeZone(data.encode())
        elif key == "url":
            return QtCore.QUrl(data)
        elif key == "bytes":
            return data.encode()
        elif key == "bytearray":
            return bytearray(data.encode())
        else:
            return obj