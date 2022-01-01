from .OutputReader import FFmpegOutputReader
from .Config import Config

from Services.Utils.WorkerThreads import WorkerThread

import subprocess


class FFmpeg:
    def __init__(self, target, saveAs):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        method = ("-c:a", "libmp3lame") if saveAs.endswith(".mp3") else ("-c", "copy")
        self.process = subprocess.Popen(
            [
                Config.PATH,
                "-y",
                "-i",
                target,
                *method,
                saveAs
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            encoding="utf-8",
            startupinfo=startupinfo
        )

    def output(self):
        return FFmpegOutputReader(self.process).reader()

    def isRunning(self):
        return self.process.poll() == None

    def wait(self):
        return self.process.communicate()

    def kill(self):
        if self.isRunning():
            self._killProcessThread = WorkerThread(target=self._killProcess)
            self._killProcessThread.start()

    def _killProcess(self):
        try:
            try:
                self.process.communicate(input="q", timeout=Config.KILL_TIMEOUT)
            except:
                self.process.kill()
                self.process.communicate()
        except:
            pass