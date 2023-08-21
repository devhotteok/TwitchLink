from .Config import Config

from Core.GlobalExceptions import Exceptions
from Services.Logging.Logger import Logger

from PyQt6 import QtCore

import enum


class FFmpeg(QtCore.QObject):
    class LogLevel(enum.Enum):
        QUIET = "quiet"
        PANIC = "panic"
        FATAL = "fatal"
        ERROR = "error"
        WARNING = "warning"
        INFO = "info"
        VERBOSE = "verbose"
        DEBUG = "debug"
        TRACE = "trace"

    started = QtCore.pyqtSignal()
    finished = QtCore.pyqtSignal()

    def __init__(self, logger: Logger, parent: QtCore.QObject | None = None):
        super().__init__(parent=parent)
        self.logger = logger
        self._process = QtCore.QProcess(parent=self)
        self._process.errorOccurred.connect(self._onProcessError)
        self._process.started.connect(self._onProcessStart)
        self._process.finished.connect(self._onProcessFinish)
        self._process.readyReadStandardError.connect(self._readStandardError)
        self._process.readyReadStandardOutput.connect(self._readStandardOutput)
        self._error: Exceptions.ProcessError | None = None
        self._closeRequested = False

    def start(self, outputTarget: str, trimFrom: int = None, trimTo: int = None, transcode: bool = False, logLevel: LogLevel = LogLevel.INFO) -> None:
        self.logger.info("Starting subprocess.")
        self._process.start(
            Config.PATH,
            (
                "-y",
                "-hide_banner",
                "-loglevel",
                logLevel.value,
                "-stats",
                *(() if trimFrom == None else ("-ss", str(trimFrom))),
                *(() if trimTo == None else ("-to", str(trimTo))),
                "-i",
                "pipe:0",
                *self._getCodecParams(fileName=outputTarget, transcode=transcode),
                outputTarget
            )
        )

    def write(self, data: bytes) -> int:
        return self._process.write(data)

    def waitForBytesWritten(self, timeout: int) -> bool:
        return self._process.waitForBytesWritten(timeout)

    def closeStream(self) -> None:
        self._closeRequested = True
        self.logger.info("Closing subprocess write channel.")
        self._process.closeWriteChannel()

    def terminate(self) -> None:
        self.logger.warning("Terminating subprocess.")
        if not self._closeRequested:
            self.closeStream()
        self._process.terminate()
        if not self._process.waitForFinished(Config.KILL_TIMEOUT):
            self.logger.warning("Subprocess was unresponsive and forced to terminate.")
            self._process.kill()

    def isRunning(self) -> bool:
        return self._process.state() != QtCore.QProcess.ProcessState.NotRunning

    def hasError(self) -> bool:
        return self._error != None

    def getError(self) -> Exceptions.ProcessError | None:
        return self._error

    def _onProcessError(self, error: QtCore.QProcess.ProcessError) -> None:
        self.logger.error(f"Subprocess error occurred.\n{error.name}: {error.value}")
        if error == QtCore.QProcess.ProcessError.FailedToStart:
            self.logger.error("Subprocess failed to start.")
            self._error = Exceptions.ProcessError(self._process)
            self.finished.emit()

    def _onProcessStart(self) -> None:
        self.logger.info("Subprocess started.")
        self.started.emit()

    def _onProcessFinish(self, exitCode: int, exitStatus: QtCore.QProcess.ExitStatus) -> None:
        if exitStatus == QtCore.QProcess.ExitStatus.NormalExit:
            self.logger.info(f"Subprocess ended with exit code {exitCode}.")
        else:
            self.logger.error(f"Subprocess crashed with exit code {exitCode}.")
            self._error = Exceptions.ProcessError(self._process)
        if self._closeRequested == False:
            self.logger.warning(f"Subprocess ended unexpectedly.")
            self._error = Exceptions.ProcessError(self._process)
        self.finished.emit()

    def _readStandardOutput(self) -> None:
        for line in self._process.readAllStandardOutput().data().decode().splitlines():
            self.logger.debug(line)

    def _readStandardError(self) -> None:
        for line in self._process.readAllStandardError().data().decode().splitlines():
            self.logger.debug(line)

    def _getCodecParams(self, fileName: str, transcode: bool = False) -> tuple[str, ...]:
        fileFormat = fileName.rsplit(".", 1)[-1]
        isAudioOnly = fileFormat in ["aac", "mp3"]
        audioCodec = self._getAudioCodecParams(fileFormat, transcode=transcode)
        return audioCodec if isAudioOnly else (*self._getVideoCodecParams(fileFormat, transcode=transcode), *audioCodec)

    def _getVideoCodecParams(self, fileFormat: str, transcode: bool = False) -> tuple[str, ...]:
        return ("-c:v", "libx264") if transcode else ("-c:v", "copy")

    def _getAudioCodecParams(self, fileFormat: str, transcode: bool = False) -> tuple[str, ...]:
        return ("-c:a", "libmp3lame") if fileFormat == "mp3" else (("-c:a", "aac") if transcode else ("-c:a", "copy"))