from Core import Qt
from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Services.Logging.Logger import Logger

from PyQt6 import QtCore, QtWidgets, QtNetwork

import types
import sys
import uuid


class ExitCode:
    UNEXPECTED_ERROR = 2
    UNEXPECTED_ERROR_RESTART = 1
    EXIT = 0
    RESTART = -1


class SingleApplicationLauncher(QtWidgets.QApplication):
    EXIT_CODE = ExitCode

    newInstanceStarted = QtCore.pyqtSignal()

    def __init__(self, appId: str, argv: list[str]):
        super().__init__(argv)
        self.setApplicationName(Config.APP_NAME)
        self.setApplicationVersion(Config.APP_VERSION)
        self.setApplicationDisplayName("")
        self.logger = Logger(fileName=f"{Config.APP_NAME}_{Logger.getFormattedTime()}#{uuid.uuid4()}.log")
        self.logger.info(f"\n\n{Config.getProjectInfo()}\n")
        self.logger.info(OSUtils.getOSInfo())
        self.shared = QtCore.QSharedMemory(appId, parent=self)
        if self.shared.create(512, QtCore.QSharedMemory.AccessMode.ReadWrite):
            self.logger.info("Application started successfully.")
            self._server = QtNetwork.QLocalServer(parent=self)
            self._server.newConnection.connect(self.newInstanceStarted)
            self._server.removeServer(appId)
            if not self._server.listen(appId):
                self.logger.warning("Failed to open Local Server.")
        else:
            self.logger.warning("Another instance of this application is already running.")
            self._socket = QtNetwork.QLocalSocket(parent=self)
            self._socket.connectToServer(appId)
            if self._socket.waitForConnected():
                self._socket.close()
            else:
                self.logger.warning("Unable to connect to Local Server.")
            sys.exit(self.EXIT_CODE.EXIT)
        self._started: QtCore.QDateTime | None = None
        self._crashed = False

    def _excepthook(self, exceptionType: type[BaseException], exception: BaseException, tracebackType: types.TracebackType | None) -> None:
        self.logger.critical("Unexpected Error", exc_info=(exceptionType, exception, tracebackType))
        if not self._crashed:
            self._crashed = True
            try:
                file = QtCore.QFile(Config.TRACEBACK_FILE, self)
                file.open(QtCore.QIODevice.OpenModeFlag.WriteOnly)
                file.write(self.logger.getPath().encode())
                file.close()
                file.deleteLater()
            except:
                pass
            self.exit(self.EXIT_CODE.UNEXPECTED_ERROR if self._started.addSecs(Config.CRASH_AUTOMATIC_RESTART_COOLDOWN) > QtCore.QDateTime.currentDateTimeUtc() else self.EXIT_CODE.UNEXPECTED_ERROR_RESTART)

    def exec(self) -> int:
        self._started = QtCore.QDateTime.currentDateTimeUtc()
        sys.excepthook = self._excepthook
        self.logger.info("Launching...")
        returnCode = super().exec()
        self.logger.info(f"Application exited with exit code {returnCode}.")
        self.logger.info(f"All logs were written to '{self.logger.getPath()}'.")
        self._server.close()
        self.shared.detach()
        return returnCode