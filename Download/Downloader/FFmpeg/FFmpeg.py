from .OutputReader import FFmpegOutputReader
from .Config import Config

from Services.Threading.WorkerThread import WorkerThread

from PyQt5 import QtCore

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

    def start(self, target, saveAs, logLevel=LogLevel.INFO, priority=Priority.NORMAL):
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
                "-i",
                target,
                *(("-c:a", "libmp3lame") if saveAs.endswith(".mp3") else ("-c", "copy")),
                saveAs
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