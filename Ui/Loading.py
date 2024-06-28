from Core.Ui import *


class Loading(QtWidgets.QDialog):
    completeSignal = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("loading", self)
        self.setWindowFlag(QtCore.Qt.WindowType.FramelessWindowHint)
        self.setWindowIcon(Icons.APP_LOGO.icon)
        self._ui.appLogo.setMargin(10)
        self._ui.appName.setText(Config.APP_NAME)
        self._ui.version.setText(f"{Config.APP_NAME} {Config.APP_VERSION}")
        self._ui.copyright.setText(Config.getCopyrightInfo())
        self.setStatus(T("loading", ellipsis=True))
        self._execAnimation = QtCore.QPropertyAnimation(parent=self)
        self._execAnimation.setTargetObject(self)
        self._execAnimation.setPropertyName(b"windowOpacity")
        self._execAnimation.setDuration(500)
        self._execAnimation.setStartValue(0)
        self._execAnimation.setEndValue(1)
        self._execAnimation.setEasingCurve(QtCore.QEasingCurve.Type.OutCubic)
        self._execAnimation.finished.connect(self._onAnimationFinish)
        self._animationFinished = False
        self._closeEnabled = False
        App.Updater.updateProgress.connect(self.updateProgress)
        App.Updater.updateComplete.connect(self._checkComplete)

    def _onAnimationFinish(self) -> None:
        self._animationFinished = True

    def updateProgress(self, progress: int) -> None:
        if progress == 0:
            self.setStatus(T("#Checking for updates", ellipsis=True))
        else:
            self.setStatus(f"{T('#Loading Data', ellipsis=True)} {progress}/3")

    def setStatus(self, status: str) -> None:
        self._ui.status.setText(status)

    def _checkComplete(self) -> None:
        if self._animationFinished:
            self.completeSignal.emit()
            self.close()
        else:
            self._execAnimation.finished.connect(self._checkComplete)

    def exec(self) -> int:
        self._execAnimation.start(QtCore.QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)
        App.Updater.update()
        return super().exec()

    def close(self) -> bool:
        self._closeEnabled = True
        return super().close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        if self._closeEnabled:
            super().closeEvent(event)
        else:
            event.ignore()