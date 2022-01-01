from Core.Updater import Updater
from Core.Ui import *


class Loading(QtWidgets.QDialog, UiFile.loading):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowIcon(QtGui.QIcon(Config.ICON_IMAGE))
        self.appLogo.setContentsMargins(10, 10, 10, 10)
        self.appLogoLoader = Utils.ImageLoader(self.appLogo, Config.LOGO_IMAGE_WHITE)
        self.appName.setText(Config.APP_NAME)
        self.version.setText("{} {}".format(Config.APP_NAME, Config.VERSION))
        self.copyright.setText(Config.getCopyrightInfo())
        self.setStatus(T("starting", ellipsis=True))
        self.loadingThread = LoadingThread()
        self.loadingThread.progressSignal.connect(self.setStatus)
        self.loadingThread.loadCompleteSignal.connect(self.close)
        self.loadingThread.start()

    def setStatus(self, status):
        self.info.setText(status)

    def close(self):
        self.closeEvent = lambda event: None
        super().close()

    def closeEvent(self, event):
        event.ignore()

class LoadingThread(QtCore.QThread):
    progressSignal = QtCore.pyqtSignal(str)
    loadCompleteSignal = QtCore.pyqtSignal()

    def run(self):
        for progress in Updater.update():
            if progress == 0:
                self.progressSignal.emit(T("#Checking for updates", ellipsis=True))
            else:
                self.progressSignal.emit("{} {}/2".format(T("#Loading Data", ellipsis=True), progress))
        self.loadCompleteSignal.emit()