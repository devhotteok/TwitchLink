from Core.Ui import *


class Setup(QtWidgets.QDialog, UiFile.setup):
    def __init__(self, parent=None):
        super(Setup, self).__init__(parent=parent)
        self.setWindowIcon(QtGui.QIcon(Icons.APP_LOGO_ICON))
        self.appLogo.setMargin(10)
        self.appName.setText(Config.APP_NAME)
        self.continueButton.clicked.connect(self.proceed)
        self.launchButton.clicked.connect(self.launch)
        self.language.addItems(Translator.getLanguageList())
        self.language.setCurrentIndex(Translator.getLanguageKeyList().index(Translator.getLanguage()))
        self.language.currentIndexChanged.connect(self.setLanguage)
        self.timezone.addItems(DB.localization.getTimezoneNameList())
        self.timezone.setCurrentText(DB.localization.getTimezone().name())
        self.timezone.currentTextChanged.connect(self.setTimezone)
        self.showTimezoneTime()
        self.timer = QtCore.QTimer(parent=self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.showTimezoneTime)
        self.timer.start()

    def setLanguage(self, index):
        Translator.setLanguage(Translator.getLanguageCode(index))

    def setTimezone(self, timezone):
        DB.localization.setTimezone(bytes(timezone, encoding="utf-8"))
        self.showTimezoneTime()

    def showTimezoneTime(self):
        self.timezoneTimeLabel.setText(QtCore.QDateTime.currentDateTimeUtc().toTimeZone(DB.localization.getTimezone()))

    def proceed(self):
        self.stackedWidget.setCurrentIndex(1)

    def launch(self):
        self.timer.stop()
        DB.setup.setupComplete()
        self.accept()