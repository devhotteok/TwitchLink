from Core.Updater import Updater
from Core.Ui import *


class Loading(QtWidgets.QDialog, UiFile.loading):
    def __init__(self, parent=None):
        super(Loading, self).__init__(parent=parent)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setWindowIcon(QtGui.QIcon(Icons.APP_LOGO_ICON))
        self.appLogo.setMargin(10)
        self.appName.setText(Config.APP_NAME)
        self.version.setText(f"{Config.APP_NAME} {Config.VERSION}")
        self.copyright.setText(Config.getCopyrightInfo())
        self.setStatus(T("loading", ellipsis=True))
        self.closeEnabled = False
        Updater.updateProgress.connect(self.updateProgress)
        self.loadingThread = Utils.WorkerThread(target=Updater.update, parent=self)
        self.loadingThread.finished.connect(self.close)
        self.loadingThread.start()

    def updateProgress(self, progress):
        if progress == 0:
            self.setStatus(T("#Checking for updates", ellipsis=True))
        elif progress == Updater.TOTAL_TASK_COUNT:
            self.setStatus(T("loading", ellipsis=True))
        else:
            self.setStatus(f"{T('#Loading Data', ellipsis=True)} {progress}/{Updater.TOTAL_TASK_COUNT - 1}")

    def setStatus(self, status):
        self.status.setText(status)

    def close(self):
        self.closeEnabled = True
        super().close()

    def closeEvent(self, event):
        if self.closeEnabled:
            super().closeEvent(event)
        else:
            event.ignore()