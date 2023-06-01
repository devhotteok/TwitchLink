from .OutputReader import FFmpegOutputReader
from .Config import Config

from Services.Threading.WorkerThread import WorkerThread

from PyQt6 import QtCore

import subprocess


class FFmpeg(QtCore.QObject):
    class LogLevel:
        QUIET = "quiet"
        PANIC = "panic"
        FATAL = "fatal"
        ERROR = "error"
        WARNING = "warning"
        INFO = "info"
        VERBOSE = "verbose"
        DEBUG = "debug"
        TRACE = "trace"


    class Priority:
        IDLE = subprocess.IDLE_PRIORITY_CLASS
        BELOW_NORMAL = subprocess.BELOW_NORMAL_PRIORITY_CLASS
        NORMAL = subprocess.NORMAL_PRIORITY_CLASS
        ABOVE_NORMAL = subprocess.ABOVE_NORMAL_PRIORITY_CLASS
        HIGH = subprocess.HIGH_PRIORITY_CLASS
        REALTIME = subprocess.REALTIME_PRIORITY_CLASS


    def __init__(self, parent=None):
        super(FFmpeg, self).__init__(parent=parent)
        self.process = None

    def startEncodingProcess(self, target, saveAs, trimFrom=None, trimTo=None, remux=True, logLevel=LogLevel.INFO, priority=Priority.NORMAL):
        self.start(
            [
                *(() if trimFrom == None else ("-ss", str(trimFrom))),
                *(() if trimTo == None else ("-to", str(trimTo))),
                "-i",
                target,
                *self.getCodecParams(fileName=saveAs, remux=remux),
                saveAs
            ],
            logLevel=logLevel,
            priority=priority
        )

    def getCodecParams(self, fileName, remux):
        fileFormat = fileName.rsplit(".", 1)[-1]
        isAudioOnly = fileFormat in ["aac", "mp3"]
        audioCodec = self.getAudioCodecParams(fileFormat, remux=remux)
        return audioCodec if isAudioOnly else (*self.getVideoCodecParams(fileFormat, remux=remux), *audioCodec)

    def getVideoCodecParams(self, fileFormat, remux):
        return ("-c:v", "copy") if remux else ("-c:v", "libx264")

    def getAudioCodecParams(self, fileFormat, remux):
        return ("-c:a", "libmp3lame") if fileFormat == "mp3" else (("-c:a", "copy") if remux else ("-c:a", "aac"))

    def start(self, params, logLevel=LogLevel.INFO, priority=Priority.NORMAL):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        self.process = subprocess.Popen(
            [
                Config.PATH,
                "-y",
                "-hide_banner",
                "-loglevel",
                logLevel,
                "-stats",
                *params
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding="utf-8",
            startupinfo=startupinfo,
            creationflags=priority
        )
        self.process.notResponding = False

    def output(self, logger=None):
        return FFmpegOutputReader(self.process, logger).reader()

    def isRunning(self):
        return self.process.poll() == None

    def wait(self):
        return self.process.communicate()

    def kill(self):
        if self.isRunning():
            self._killProcessThread = WorkerThread(target=self._killProcess, parent=self)
            self._killProcessThread.start()

    def _killProcess(self):
        try:
            self.process.communicate(input="q", timeout=Config.KILL_TIMEOUT)
        except:
            self.process.notResponding = True
            try:
                self.process.kill()
                self.process.communicate()
            except:
                pass