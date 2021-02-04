import threading
import subprocess

from Services.Twitch.TwitchPlaybackAccessTokens import *


class TwitchDownloaderNetworkError(Exception):
    def __str__(self):
        return "\nNetwork Error"

class TwitchDownloader:
    FILE_READER = re.compile("#EXTINF:(\d*\.?\d*),")
    FILE_PROGRESS = re.compile("\[.* @ .*\] Opening \'.*\' for reading")
    TIME_PROGRESS = re.compile(".*size=.*time=(.*)bitrate=.*speed=.*")

    def __init__(self, ffmpeg, download_type, url, file_path):
        self.ffmpeg = ffmpeg
        self.download_type = download_type
        self.url = url
        self.file_path = file_path
        self.process = None
        self.error = False
        self.done = False
        self.canceled = False
        self.fileProgress = 0
        self.timeProgress = "00:00:00"
        if self.download_type == "video":
            self.checkPlaylist()
            self.setRange(None, None)
        else:
            self.totalFiles = 0
            self.totalSeconds = 0
            self.totalTime = "00:00:00"

    def checkPlaylist(self):
        try:
            data = requests.get(self.url)
            if data.status_code != 200:
                raise
        except:
            raise TwitchDownloaderNetworkError
        fileLength = list(map(float, re.findall(self.FILE_READER, data.text)))
        self.realTotalFiles = len(fileLength)
        self.realTotalSeconds = int(sum(fileLength))
        self.totalFiles = self.realTotalFiles
        self.totalSeconds = self.realTotalSeconds
        self.reloadTotalTime()

    def setRange(self, start, end):
        if self.download_type == "video":
            self.range = {"start": start, "end": end}
            if start == None:
                start = 0
            if end == None:
                end = self.realTotalSeconds
            self.totalSeconds = end - start
            self.totalFiles = int((self.totalSeconds / self.realTotalSeconds) * self.realTotalFiles)
            self.reloadTotalTime()

    def reloadTotalTime(self):
        h = str(self.totalSeconds // 3600)
        h = (2 - len(h)) * "0" + h
        m = str(self.totalSeconds % 3600 // 60)
        m = (2 - len(m)) * "0" + m
        s = str(self.totalSeconds % 3600 % 60)
        s = (2 - len(s)) * "0" + s
        self.totalTime = h + ":" + m + ":" + s

    def download(self):
        downloader = threading.Thread(target=self.downloader)
        downloader.start()

    def downloader(self):
        ffmpeg = [self.ffmpeg, "-y"]
        if self.download_type == "video":
            if self.range["start"] != None:
                ffmpeg.extend(["-ss", str(self.range["start"])])
            if self.range["end"] != None:
                ffmpeg.extend(["-to", str(self.range["end"])])
        ffmpeg.extend(["-i", self.url, "-c", "copy", self.file_path])
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.process = subprocess.Popen(ffmpeg, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding="utf-8", startupinfo=startupinfo)
            for line in self.process.stdout:
                fileCheck = re.search(self.FILE_PROGRESS, line)
                if fileCheck != None:
                    self.fileProgress += 1
                if self.fileProgress > self.totalFiles:
                    self.totalFiles = self.fileProgress
                timeCheck = re.search(self.TIME_PROGRESS, line)
                if timeCheck != None:
                    self.timeProgress = timeCheck.group(1).strip().split(".")[0]
        except:
            self.error = True
            self.canceled = True
        self.done = True

    def cancelDownload(self):
        if self.process != None:
            if self.done == False:
                self.process.kill()
                self.canceled = True