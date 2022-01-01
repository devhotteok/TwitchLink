from .Setup import EngineSetup

from Core.GlobalExceptions import Exceptions

from Services.NetworkRequests import requests
from Services.Utils.Utils import Utils


class ClipDownloader(EngineSetup):
    def run(self):
        try:
            self.download()
        except:
            self.status.raiseError(Exceptions.NetworkError)
        self.status.setDone()
        self.syncStatus()

    def download(self):
        response = requests.get(self.setup.downloadInfo.getUrl(), stream=True)
        if response.status_code == 200:
            self.progress.totalByteSize = int(response.headers.get("Content-Length", 0))
            self.progress.totalSize = Utils.formatByteSize(self.progress.totalByteSize)
            self.status.setDownloading()
            self.syncStatus()
            try:
                with open(self.setup.downloadInfo.getAbsoluteFileName(), "wb") as file:
                    loopCount = 0
                    for data in response.iter_content(1024):
                        file.write(data)
                        self.progress.byteSize += len(data)
                        self.progress.size = Utils.formatByteSize(self.progress.byteSize)
                        if loopCount % 1024 == 0:
                            self.syncProgress()
                        loopCount += 1
                    self.syncProgress()
            except:
                self.status.raiseError(Exceptions.FileSystemError)
            else:
                if self.progress.byteSize != self.progress.totalByteSize:
                    raise
        else:
            raise

    def cancel(self):
        pass