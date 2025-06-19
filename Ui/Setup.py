from Core.Ui import *


class Setup(QtWidgets.QDialog):
    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self._ui = UiLoader.load("setup", self)
        self.setWindowIcon(Icons.APP_LOGO.icon)
        self._ui.appLogo.setMargin(10)
        self._ui.appName.setText(Config.APP_NAME)
        self._ui.continueButton.clicked.connect(self.proceed)
        self._ui.launchButton.clicked.connect(self.launch)
        for translationPack in App.Translator.getTranslationPacks():
            self._ui.language.addItem(translationPack.getDisplayName(), userData=translationPack.getId())
        self._ui.language.setCurrentIndex(self._ui.language.findData(App.Translator.getCurrentTranslationPackId()))
        self._ui.language.currentIndexChanged.connect(self.updateLanguage)
        self._ui.timezone.addItems(App.Preferences.localization.getTimezoneNameList())
        self._ui.timezone.setCurrentText(App.Preferences.localization.getTimezone().name())
        self._ui.timezone.currentTextChanged.connect(self.setTimezone)
        self.showTimezoneTime()
        self.timer = QtCore.QTimer(parent=self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.showTimezoneTime)
        self.timer.start()

    def updateLanguage(self) -> None:
        App.Translator.setTranslationPack(self._ui.language.currentData())

    def setTimezone(self, timezone: str) -> None:
        App.Preferences.localization.setTimezone(bytes(timezone, encoding="utf-8"))
        self.showTimezoneTime()

    def showTimezoneTime(self) -> None:
        self._ui.timezoneTimeLabel.setText(QtCore.QDateTime.currentDateTimeUtc())

    def proceed(self) -> None:
        self._ui.stackedWidget.setCurrentIndex(1)

    def launch(self) -> None:
        self.timer.stop()
        App.Preferences.setup.setupComplete()
        self.accept()