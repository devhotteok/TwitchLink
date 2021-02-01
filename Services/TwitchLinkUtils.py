import os
import requests
import threading
import re

from PyQt5.QtGui import QIcon, QPixmap, QImage
from PyQt5.QtWidgets import QMessageBox, QFileDialog

from TwitchLinkConfig import Config

from Services.TwitchLinkTranslator import translator, T


class NoDefaultImage(Exception):
    def __str__(self):
        return "\nDefault Image Not Found"

class IMAGE_CACHE:
    IMAGES = {}

class Utils:
    @staticmethod
    def info(infoTitle, infoText, **kwargs):
        infoTitle = T(infoTitle, **kwargs)
        infoText = T(infoText, **kwargs)
        info = QMessageBox()
        info.setWindowIcon(QIcon(Config.LOGO_IMAGE))
        info.setWindowTitle(infoTitle)
        info.setIcon(QMessageBox.Information)
        info.setText(infoText)
        info.setStandardButtons(QMessageBox.Ok)
        info.setFont(translator.getFont())
        info.exec()

    @staticmethod
    def ask(askTitle, askText, okText=None, cancelText=None, defaultOk=False, **kwargs):
        askTitle = T(askTitle, **kwargs)
        askText = T(askText, **kwargs)
        ask = QMessageBox()
        ask.setWindowIcon(QIcon(Config.LOGO_IMAGE))
        ask.setWindowTitle(askTitle)
        ask.setIcon(QMessageBox.Information)
        ask.setText(askText)
        ask.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        if okText != None:
            ask.button(QMessageBox.Ok).setText(T(okText))
        if cancelText != None:
            ask.button(QMessageBox.Cancel).setText(T(cancelText))
        if defaultOk:
            ask.setDefaultButton(QMessageBox.Ok)
        else:
            ask.setDefaultButton(QMessageBox.Cancel)
        ask.setFont(translator.getFont())
        return ask.exec() == QMessageBox.Ok

    @staticmethod
    def safeFormat(string, **kwargs):
        index = 0
        while index < len(string):
            for key, value in kwargs.items():
                key = "{" + key + "}"
                value = str(value)
                if string[index:].startswith(key):
                    string = string[:index] + str(value) + string[index + len(key):]
                    index += len(value) - 1
                    break
            index += 1
        return string

    @staticmethod
    def askFileDirectory(parent, directory):
        fileDialog = QFileDialog()
        fileDialog.setWindowIcon(QIcon(Config.LOGO_IMAGE))
        return fileDialog.getExistingDirectory(parent, T("#{name} - Select Folder", name=T("#PROGRAM_NAME")), directory)

    @staticmethod
    def askSaveDirectory(parent, directory, filters, initialFilter):
        fileDialog = QFileDialog()
        fileDialog.setWindowIcon(QIcon(Config.LOGO_IMAGE))
        return fileDialog.getSaveFileName(parent, T("#{name} - Save As", name=T("#PROGRAM_NAME")), directory, filters, initialFilter)[0]

    @staticmethod
    def createDirectory(directory):
        if not Utils.checkDirectoryExists(directory):
            os.makedirs(directory)

    @staticmethod
    def checkDirectoryExists(directory):
        return os.path.isdir(directory)

    @staticmethod
    def checkFileExists(file):
        return os.path.isfile(file)

    @staticmethod
    def parseTwitchUrl(url):
        CHANNEL_URL = re.compile("twitch\.tv\/([a-zA-Z0-9]+)")
        VIDEO_URL = re.compile("twitch\.tv\/videos\/(\d+)")
        CLIP_URL = re.compile("(?:clips.twitch\.tv\/|twitch\.tv\/(?:[a-zA-Z0-9]+)\/clip\/)([^?\n]+)")
        check = re.search(VIDEO_URL, url)
        if check != None:
            return "video_id", check.group(1)
        check = re.search(CLIP_URL, url)
        if check != None:
            return "clip_id", check.group(1)
        check = re.search(CHANNEL_URL, url)
        if check != None:
            return "channel_id", check.group(1)
        return None, None

    @staticmethod
    def getTotalSeconds(duration):
        time = duration.split(":")
        return int(time[0]) * 3600 + int(time[1]) * 60 + int(time[2])

    @staticmethod
    def getDocs(language, file):
        try:
            with open("{}/{}/{}.html".format(Config.DOCS_ROOT, language, file), "r", encoding="utf-8") as file:
                return file.read()
        except:
            return T("#Failed to load data.")

    @staticmethod
    def Image(url, default=None):
        if url == "" or url == None:
            if default == None:
                raise NoDefaultImage
            return QPixmap(default)
        elif url.startswith("http://") or url.startswith("https://"):
            if default == None:
                raise NoDefaultImage
            DEFAULT_SIZE = [
                ("https://static-cdn.jtvnw.net/jtv_user_pictures", None),
                ("https://static-cdn.jtvnw.net/ttv-boxart", (90, 120)),
                ("https://static-cdn.jtvnw.net/previews-ttv", (1920, 1080)),
                ("https://static-cdn.jtvnw.net/cf_vods", (1920, 1080)),
                ("https://clips-media-assets2.twitch.tv", None)
            ]
            for serverUrl, size in DEFAULT_SIZE:
                if url.startswith(serverUrl):
                    if size != None:
                        url = url.format(width=size[0], height=size[1])
                    break
            url = url.replace("-%{width}x%{height}", "")
            url = url.replace("-260x147", "")
            if url in IMAGE_CACHE.IMAGES:
                return IMAGE_CACHE.IMAGES[url]
            try:
                data = requests.get(url)
                if data.status_code == 200:
                    image = QImage()
                    image.loadFromData(data.content)
                    pixmap = QPixmap(image)
                    IMAGE_CACHE.IMAGES[url] = pixmap
                    return pixmap
                else:
                    raise
            except:
                return QPixmap(default)
        else:
            return QPixmap(url)

    class FileDownloader:
        def __init__(self, url, file):
            self.url = url
            self.file = file
            self.progress = 0
            self.failed = False
            self.reason = None
            self.done = False
            self.thread = threading.Thread(target=self.download)
            self.thread.start()

        def download(self):
            try:
                response = requests.get(self.url, stream=True)
                if response.status_code == 200:
                    total_size = int(response.headers.get('Content-Length'))
                    current_size = 0
                    try:
                        with open(self.file, "wb") as file:
                            for data in response.iter_content(1024):
                                file.write(data)
                                current_size += len(data)
                                self.progress = int((current_size / total_size) * 100)
                    except:
                        self.reason = "FileError"
                        self.failed = True
                        self.done = True
                        return
                    if self.progress != 100:
                        raise
                else:
                    raise
            except:
                self.reason = "NetworkError"
                self.failed = True
            self.done = True