class FileNameManager:
    lockedFileNames = []

    @classmethod
    def getLockedFileNames(cls):
        return cls.lockedFileNames

    @classmethod
    def isAvailable(cls, absoluteFileName):
        return absoluteFileName not in cls.lockedFileNames

    @classmethod
    def lock(cls, absoluteFileName):
        cls.lockedFileNames.append(absoluteFileName)

    @classmethod
    def unlock(cls, absoluteFileName):
        cls.lockedFileNames.remove(absoluteFileName)