from .Config import Config

from Core.GlobalExceptions import Exceptions
from Services.Utils.OSUtils import OSUtils
from Services.Logging.Logger import Logger

from PyQt6 import QtCore

import os


class SafeTempDirectory(QtCore.QObject):
    def __init__(self, directory: str, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self._error: Exceptions.FileSystemError | None = None
        self._directory = QtCore.QTemporaryDir(OSUtils.joinPath(directory, Config.DIRECTORY_PREFIX))
        if not self._directory.isValid():
            self._raiseException(Exceptions.FileSystemError(self._directory))
            return
        try:
            OSUtils.hideFileOrDirectory(self._directory.path())
        except:
            pass
        self._keyFile = QtCore.QTemporaryFile(OSUtils.joinPath(Config.TEMP_LIST_DIRECTORY, Config.TEMP_KEY_FILE_PREFIX), self)
        if not self._keyFile.open() or self._keyFile.write(self._directory.path().encode()) == -1:
            self._directory.remove()
            self._raiseException(Exceptions.FileSystemError(self._keyFile))
            return
        self._keyFile.close()
        self._dirLock = QtCore.QFile(OSUtils.joinPath(self._directory.path(), Config.DIRECTORY_LOCK_FILE_NAME), self)
        if not self._dirLock.open(QtCore.QFile.OpenModeFlag.ReadWrite):
            self._directory.remove()
            self._raiseException(Exceptions.FileSystemError(self._dirLock))

    def _raiseException(self, exception: Exception) -> None:
        self._error = exception

    def getError(self) -> Exceptions.FileSystemError | None:
        return self._error

    def path(self) -> str:
        return self._directory.path()

    def __del__(self):
        try:
            if self.getError() == None:
                self._dirLock.close()
        except:
            pass


class TempManager(QtCore.QObject):
    def __init__(self, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.logger = logger
        try:
            OSUtils.createDirectory(Config.TEMP_LIST_DIRECTORY)
            self.cleanup()
        except:
            pass

    def cleanup(self) -> None:
        files = os.listdir(Config.TEMP_LIST_DIRECTORY)
        if len(files) == 0:
            return
        else:
            self.logger.info("Cleaning up temp files.")
        for filename in files:
            path = OSUtils.joinPath(Config.TEMP_LIST_DIRECTORY, filename)
            try:
                self.cleanTempDirKeyFile(path)
            except Exception as e:
                self.logger.exception(e)

    def cleanTempDirKeyFile(self, tempDirKeyFile: str) -> None:
        if OSUtils.isFile(tempDirKeyFile):
            file = QtCore.QFile(tempDirKeyFile, self)
            if file.open(QtCore.QIODevice.OpenModeFlag.ReadOnly):
                tempDir = file.readAll().data().decode()
                if OSUtils.isDirectory(tempDir):
                    self.logger.info(f"Removing temp directory: {tempDir}")
                    OSUtils.removeDirectory(tempDir)
            file.remove()
            file.deleteLater()