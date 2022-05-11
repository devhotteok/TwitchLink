from Core import Qt
from Core.Config import Config
from Services.Utils.OSUtils import OSUtils
from Services.Logging.Logger import Logger

from PyQt5 import QtCore, QtWidgets, QtNetwork

import sys


class ExitCode:
    UNEXPECTED_ERROR = 1
    EXIT = 0
    RESTART = -1


class SingleApplicationLauncher(QtWidgets.QApplication):
    EXIT_CODE = ExitCode

    def __init__(self, guid, argv):
        super(SingleApplicationLauncher, self).__init__(argv)
        self.logger = Logger(fileName=f"{Config.APP_NAME}_{id(self)}.txt")
        self.logger.info(f"\n\n{Config.getProjectInfo()}\n")
        self.logger.info(OSUtils.getOSInfo())
        self.shared = QtCore.QSharedMemory(guid, parent=self)
        if self.shared.create(512, QtCore.QSharedMemory.ReadWrite):
            self.logger.info("Application started successfully.")
            self._server = QtNetwork.QLocalServer(parent=self)
            self.newInstanceStarted = self._server.newConnection
            self._server.listen(guid)
            sys.excepthook = self.excepthook
        else:
            self.logger.error("Another instance of this application is already running.")
            self._socket = QtNetwork.QLocalSocket(parent=self)
            self._socket.connectToServer(guid)
            self._socket.waitForConnected()
            sys.exit(self.EXIT_CODE.EXIT)

    def exec(self):
        self.logger.info("Launching...")
        returnCode = super().exec()
        self.logger.info(f"Application exited with exit code {returnCode}.")
        self.logger.info(f"All logs were written to '{self.logger.getPath()}'.")
        return returnCode

    def excepthook(self, exc_type, exc_value, exc_tb):
        self.logger.exception("Unexpected Error", exc_info=(exc_type, exc_value, exc_tb))
        self.exit(self.EXIT_CODE.UNEXPECTED_ERROR)