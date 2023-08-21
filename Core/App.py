from Core.Launcher import SingleApplicationLauncher
from Core.SystemTrayIcon import SystemTrayIcon
from Core.Notification import Notification
from Core.Config import Config

from PyQt6 import QtCore, QtWidgets

import sys


class App(SingleApplicationLauncher):
    appStarted = QtCore.pyqtSignal()

    def __init__(self, appId: str, argv: list[str]):
        super().__init__(appId, argv)
        self.systemTrayIcon = SystemTrayIcon(parent=self)
        self.notification = Notification(self.systemTrayIcon, parent=self)
        self.mainWindow: QtWidgets.QMainWindow | None = None

    def start(self, mainWindow: QtWidgets.QMainWindow) -> int:
        self.mainWindow = mainWindow
        self.appStarted.emit()
        exitCode = self.exec()
        self.mainWindow = None
        return exitCode

    def exit(self, exitCode: int = 0) -> None:
        super().exit(exitCode)

    def restart(self) -> None:
        self.exit(self.EXIT_CODE.RESTART)

Instance = App(Config.APP_ROOT, sys.argv)


from Services.NetworkAccessManager import NetworkAccessManager as _NetworkAccessManager
NetworkAccessManager = _NetworkAccessManager(parent=Instance)

from Services.Twitch.GQL.TwitchGQLAPI import TwitchGQL as _TwitchGQL
TwitchGQL = _TwitchGQL(parent=Instance)

from Services.Translator.Translator import Translator as _Translator
Translator = _Translator(parent=Instance)
T = Translator.translate

from Services.NotificationManager import NotificationManager as _NotificationManager
Notifications = _NotificationManager(parent=Instance)

from Services.ContentManager import ContentManager as _ContentManager
ContentManager = _ContentManager(parent=Instance)

from Services.Temp.TempManager import TempManager as _TempManager
TempManager = _TempManager(logger=Instance.logger, parent=Instance)

from Services.Image.Loader import ImageLoader as _ImageLoader
ImageLoader = _ImageLoader(parent=Instance)

from Services.PartnerContent.PartnerContentManager import PartnerContentManager as _PartnerContentManager
PartnerContentManager = _PartnerContentManager(parent=Instance)

from Services.Twitch.Authentication.Integrity.IntegrityGenerator import TwitchIntegrityGenerator as _TwitchIntegrityGenerator
TwitchIntegrityGenerator = _TwitchIntegrityGenerator(logger=Instance.logger, parent=Instance)

from Services.Account.TwitchAccount import TwitchAccount as _TwitchAccount
Account = _TwitchAccount(parent=Instance)

from Download.Downloader.Core.Engine.File.FileDownloadManager import FileDownloadManager as _FileDownloadManager
FileDownloadManager = _FileDownloadManager(parent=Instance)

from Download.DownloadManager import DownloadManager as _DownloadManager
DownloadManager = _DownloadManager(parent=Instance)

from Download.ScheduledDownloadPubSubManager import ScheduledDownloadPubSubManager as _ScheduledDownloadPubSubManager
ScheduledDownloadPubSubManager = _ScheduledDownloadPubSubManager(logger=Instance.logger, parent=Instance)

from Download.ScheduledDownloadManager import ScheduledDownloadManager as _ScheduledDownloadManager
ScheduledDownloadManager = _ScheduledDownloadManager(parent=Instance)

from Download.GlobalDownloadManager import GlobalDownloadManager as _GlobalDownloadManager
GlobalDownloadManager = _GlobalDownloadManager(parent=Instance)

from Download.History.DownloadHistoryManager import DownloadHistoryManager as _DownloadHistoryManager
DownloadHistory = _DownloadHistoryManager(parent=Instance)

from Core.Updater import Updater as _Updater
Updater = _Updater(parent=Instance)

from AppData.Preferences import Preferences as _Preferences
Preferences = _Preferences(logger=Instance.logger, parent=Instance)
Preferences.load()