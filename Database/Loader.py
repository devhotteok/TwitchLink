from .Updater import Converters


class _DataManager:
    def unpack(self, data):
        return self.unpackItems(data.items())

    def unpackItems(self, items):
        return {key: self.itemsToDict(value) for key, value in items}

    def itemsToDict(self, data):
        if hasattr(data, "__dict__"):
            return self.unpackItems(data.__dict__.items())
        else:
            return data

    def pack(self, dataObject, data):
        for key, value in data.items():
            if hasattr(dataObject, key):
                if not isinstance(getattr(dataObject, key), dict) and isinstance(value, dict):
                    self.pack(getattr(dataObject, key), value)
                else:
                    setattr(dataObject, key, value)
        return dataObject


class _DatabaseLoader(_DataManager):
    def load(self, database, data):
        try:
            self.database = database
            self.data = data
            for converter in Converters.getConverters(self.getOldVersion()):
                self.data = converter(self.data)
            return self.pack(self.database, self.data)
        except:
            return database

    def getOldVersion(self):
        try:
            return self.data["version"]
        except:
            return ""

DatabaseLoader = _DatabaseLoader()