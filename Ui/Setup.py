from Core.Ui import *

import datetime


class Setup(QtWidgets.QDialog, UiFile.setup):
    def __init__(self, parent=None):
        super(Setup, self).__init__(parent=parent)
        self.setWindowIcon(QtGui.QIcon(Icons.APP_LOGO_ICON))
        self.appLogo.setMargin(10)
        self.appName.setText(Config.APP_NAME)
        self.continueButton.clicked.connect(self.proceed)
        self.launchButton.clicked.connect(self.launch)
        self.language.addItems(Translator.getLanguageList())
        self.language.setCurrentIndex(Translator.getLanguageKeyList().index(DB.localization.getLanguage()))
        self.language.currentIndexChanged.connect(self.setLanguage)
        self.timezone.addItems(DB.localization.getTimezoneList())
        self.timezone.setCurrentText(DB.localization.getTimezone().zone)
        self.timezone.currentTextChanged.connect(self.setTimezone)
        self.showTimezoneTime()
        self.timer = QtCore.QTimer(parent=self)
        self.timer.setInterval(100)
        self.timer.timeout.connect(self.showTimezoneTime)
        self.timer.start()

    def setLanguage(self, index):
        DB.localization.setLanguage(Translator.getLanguageCode(index))

    def setTimezone(self, timezone):
        DB.localization.setTimezone(timezone)
        self.showTimezoneTime()

    def showTimezoneTime(self):
        self.timezoneTimeLabel.setText(datetime.datetime.now(tz=DB.localization.getTimezone()))

    def proceed(self):
        self.stackedWidget.setCurrentIndex(1)

    def launch(self):
        self.timer.stop()
        DB.setup.setupComplete()
        self.accept()