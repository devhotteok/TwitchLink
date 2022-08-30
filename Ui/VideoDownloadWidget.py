from Core.Ui import *
from Services.Twitch.Gql import TwitchGqlModels
from Ui.Components.Widgets.DownloadButton import DownloadButton
from Ui.Components.Widgets.InstantDownloadButton import InstantDownloadButton


class VideoDownloadWidget(QtWidgets.QWidget, UiFile.videoDownloadWidget):
    accountPageShowRequested = QtCore.pyqtSignal()

    def __init__(self, data, resizable=True, parent=None):
        super(VideoDownloadWidget, self).__init__(parent=parent)
        self.videoData = data
        self.videoType = type(self.videoData)
        self.videoWidget = Utils.setPlaceholder(self.videoWidget, Ui.VideoWidget(self.videoData, resizable=resizable, parent=self))
        self.downloadButtonManager = DownloadButton(self.videoData, self.downloadButton, buttonText=T("live-download" if self.videoType == TwitchGqlModels.Channel or self.videoType == TwitchGqlModels.Stream else "download"), parent=self)
        self.downloadButtonManager.accountPageShowRequested.connect(self.accountPageShowRequested)
        self.instantDownloadButtonManager = InstantDownloadButton(self.videoData, self.instantDownloadButton, parent=self)
        self.instantDownloadButtonManager.accountPageShowRequested.connect(self.accountPageShowRequested)