class Exceptions:
    class FileNameUnavailable(Exception):
        def __str__(self):
            return "File Name Unavailable"


class FileNameManager:
    lockedFileNames = []

    def __init__(self, absoluteFileName):
        self.absoluteFileName = absoluteFileName

    def __enter__(self):
        self.lockedFileNames.append(self.absoluteFileName)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.lockedFileNames.remove(self.absoluteFileName)

    @classmethod
    def getLockedFileNames(cls):
        return cls.lockedFileNames

    @classmethod
    def isAvailable(cls, absoluteFileName):
        return absoluteFileName not in cls.lockedFileNames

    @classmethod
    def lock(cls, absoluteFileName):
        if cls.isAvailable(absoluteFileName):
            return FileNameManager(absoluteFileName)
        else:
            raise Exceptions.FileNameUnavailable