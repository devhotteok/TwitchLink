class Exceptions:
    class FileNameUnavailable(Exception):
        def __str__(self):
            return "File Name Unavailable"


class FileNameLocker:
    lockedFiles = []

    def __init__(self, absoluteFileName: str):
        self.absoluteFileName = absoluteFileName
        self.locked = False

    def lock(self) -> None:
        if self.locked == False:
            if self.isAvailable(self.absoluteFileName):
                self.lockedFiles.append(self.absoluteFileName)
                self.locked = True
            else:
                raise Exceptions.FileNameUnavailable

    def unlock(self) -> None:
        if self.locked == True:
            self.lockedFiles.remove(self.absoluteFileName)
            self.locked = False

    def __enter__(self):
        self.lock()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unlock()

    @classmethod
    def getLockedFiles(cls) -> list[str]:
        return cls.lockedFiles

    @classmethod
    def isAvailable(cls, absoluteFileName: str) -> bool:
        return absoluteFileName not in cls.lockedFiles