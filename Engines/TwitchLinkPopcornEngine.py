import threading
import subprocess
import time

from shutil import rmtree

from Services.Twitch.TwitchPlaybackAccessTokens import *


class TwitchDownloaderNetworkError(Exception):
    def __str__(self):
        return "\nNetwork Error"

class TwitchDownloaderFileSystemError(Exception):
    def __str__(self):
        return "\nFile System Error"

class TwitchDownloader:
    FILE_READER = re.compile("#EXTINF:(\d*\.?\d*),")
    TIME_PROGRESS = re.compile(".*size=.*time=(.*)bitrate=.*speed=.*")
    THREAD_LIMIT = 20

    def __init__(self, ffmpeg, url, file_path, data_path, fast_download, update_tracking):
        self.ffmpeg = ffmpeg
        self.url = url
        self.file_path = file_path
        self.data_path = data_path
        self.fast_download = fast_download
        self.update_tracking = update_tracking
        self.process = None
        self.error = False
        self.done = False
        self.cancel = False
        self.canceled = False
        self.waiting = False
        self.fileProgress = 0
        self.timeProgress = "00:00:00"
        self.checkPlaylist()

    def checkPlaylist(self):
        try:
            data = requests.get(self.url)
            if data.status_code != 200:
                raise
        except:
            raise TwitchDownloaderNetworkError
        playlist = re.sub("(.*)-(?:un|)muted\.ts", "\\1.ts", data.text)
        try:
            with open(self.data_path + "/" + "index-dvr.m3u8", "w") as file:
                file.write(playlist)
        except:
            raise TwitchDownloaderFileSystemError
        fileLength = list(map(float, re.findall(self.FILE_READER, data.text)))
        self.totalFiles = len(fileLength)
        self.totalSeconds = int(sum(fileLength))
        self.reloadTotalTime()
        self.downloadList = re.findall(".*\.ts", playlist)

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
        file_url = "/".join(self.url.split("/")[:-1])
        downloadedList = []
        while True:
            if self.fast_download:
                downloadThreads = []
                runningThreads = []
                for file in self.downloadList:
                    if file not in downloadedList:
                        downloadedList.append(file)
                        downloadThreads.append(threading.Thread(target=self.downloadFile, args=(file_url, file)))
                for thread in downloadThreads:
                    if self.cancel:
                        break
                    while True:
                        if self.cancel:
                            break
                        time.sleep(0.1)
                        index = 0
                        while index < len(runningThreads):
                            if runningThreads[index].is_alive():
                                index += 1
                            else:
                                del runningThreads[index]
                                self.fileProgress += 1
                        if len(runningThreads) < self.THREAD_LIMIT:
                            break
                    runningThreads.append(thread)
                    thread.start()
                while len(runningThreads) > 0:
                    time.sleep(0.1)
                    index = 0
                    while index < len(runningThreads):
                        if runningThreads[index].is_alive():
                            index += 1
                        else:
                            del runningThreads[index]
                            self.fileProgress += 1
            else:
                currentDownloadList = []
                for file in self.downloadList:
                    if file not in downloadedList:
                        downloadedList.append(file)
                        currentDownloadList.append(file)
                for file in currentDownloadList:
                    if self.cancel:
                        self.startCancel()
                        return
                    self.downloadFile(file_url, file)
                    self.fileProgress += 1
            if self.cancel:
                self.startCancel()
                return
            if not self.update_tracking:
                break
            self.waiting = True
            for i in range(300):
                if self.cancel:
                    self.startCancel()
                    return
                time.sleep(1)
            self.waiting = False
            if self.cancel:
                self.startCancel()
                return
            totalSeconds = self.totalSeconds
            self.checkPlaylist()
            if totalSeconds == self.totalSeconds:
                break
        if self.cancel:
            self.startCancel()
        else:
            self.encoder()

    def startCancel(self):
        self.removeTemporaryFiles()
        self.canceled = True
        self.done = True

    def downloadFile(self, file_url, file_name):
        try:
            self.fileDownloader(file_url, file_name)
        except TwitchDownloaderNetworkError:
            pass
        except TwitchDownloaderFileSystemError:
            self.error = True
            self.cancel = True

    def fileDownloader(self, file_url, file_name):
        unmuted = file_name.replace(".ts", "-unmuted.ts")
        muted = file_name.replace(".ts", "-muted.ts")
        for check_file in [file_name, unmuted, muted]:
            try:
                response = requests.get(file_url + "/" + check_file)
                if response.status_code != 200:
                    raise
            except:
                continue
            try:
                with open(self.data_path + "/" + file_name, "wb") as file:
                    file.write(response.content)
                    return
            except:
                raise TwitchDownloaderFileSystemError
        raise TwitchDownloaderNetworkError

    def encoder(self):
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            self.process = subprocess.Popen([self.ffmpeg, "-y", "-i", self.data_path + "/" + "index-dvr.m3u8", "-c", "copy", self.file_path], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True, encoding="utf-8", startupinfo=startupinfo)
            for line in self.process.stdout:
                timeCheck = re.search(self.TIME_PROGRESS, line)
                if timeCheck != None:
                    self.timeProgress = timeCheck.group(1).strip().split(".")[0]
        except:
            self.error = True
            self.cancel = True
            self.canceled = True
            print("error")
        self.removeTemporaryFiles()
        self.done = True

    def removeTemporaryFiles(self):
        try:
            rmtree(self.data_path)
        except:
            pass

    def cancelDownload(self):
        self.cancel = True
        if self.process != None:
            if self.done == False:
                self.process.kill()
                self.canceled = True
        while not self.canceled:
            pass