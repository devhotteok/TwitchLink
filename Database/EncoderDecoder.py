import datetime
import pytz


class ObjectData(dict):
    pass


class Encoder:
    @classmethod
    def encode(cls, obj):
        if isinstance(obj, str):
            return f"str:{obj}"
        elif isinstance(obj, datetime.datetime):
            return f"datetime:{obj.isoformat()}"
        elif isinstance(obj, datetime.date):
            return f"date:{obj.isoformat()}"
        elif isinstance(obj, datetime.time):
            return f"time:{obj.isoformat()}"
        elif isinstance(obj, datetime.timedelta):
            return f"timedelta:{obj.total_seconds()}"
        elif isinstance(obj, pytz.BaseTzInfo):
            return f"timezone:{obj.zone}"
        elif isinstance(obj, bytes):
            return f"bytes:{obj.decode()}"
        elif isinstance(obj, bytearray):
            return f"bytearray:{obj.decode()}"
        elif isinstance(obj, (list, tuple)):
            return cls.encodeList(obj)
        elif isinstance(obj, dict):
            return cls.encodeDict(obj)
        elif cls.isObjectType(obj):
            return cls.encodeObject(obj)
        else:
            return obj

    @classmethod
    def encodeList(cls, obj):
        return [cls.encode(data) for data in obj]

    @classmethod
    def encodeDict(cls, obj):
        data = {key: cls.encode(value) for key, value in obj.items()}
        data["__type__"] = "dict"
        return data

    @classmethod
    def encodeObject(cls, obj):
        data = {key: cls.encode(value) for key, value in obj.__dict__.items()}
        data["__type__"] = "obj"
        return data

    @classmethod
    def isObjectType(cls, obj):
        return hasattr(obj, "__dict__")


class Decoder:
    @classmethod
    def decode(cls, obj):
        if isinstance(obj, list):
            obj = cls.decodeList(obj)
        elif isinstance(obj, dict):
            obj = cls.decodeDict(obj)
        elif isinstance(obj, str):
            obj = cls.decodeString(obj)
        return obj

    @classmethod
    def decodeList(cls, obj):
        for index in range(len(obj)):
            obj[index] = cls.decode(obj[index])
        return obj

    @classmethod
    def decodeDict(cls, obj):
        if obj.pop("__type__", "dict") == "obj":
            targetObject = ObjectData()
        else:
            targetObject = obj
        for key in obj:
            targetObject[key] = cls.decode(obj[key])
        return targetObject

    @classmethod
    def decodeString(cls, obj):
        key, data = obj.split(":", 1)
        if key == "str":
            return data
        elif key == "datetime":
            return datetime.datetime.fromisoformat(data)
        elif key == "date":
            return datetime.date.fromisoformat(data)
        elif key == "time":
            return datetime.time.fromisoformat(data)
        elif key == "timedelta":
            return datetime.timedelta(seconds=float(data))
        elif key == "timezone":
            return pytz.timezone(data)
        elif key == "bytes":
            return data.encode()
        elif key == "bytearray":
            return bytearray(data.encode())
        else:
            return obj