from Core.App import App
from Core.Ui import *


class TermsOfService(QtWidgets.QDialog, UiFile.termsOfService):
    def __init__(self):
        super().__init__(parent=App.getActiveWindow())
        self.selectLanguage.setText(" / ".join(Translator.getLanguageList()))
        self.selectLanguage.clicked.connect(lambda: App.coreWindow().openSettings(page=1))
        self.textBrowser.setHtml(Utils.getDocs("TermsOfService", DB.localization.getLanguage(), appName=Config.APP_NAME, copyright=Config.getCopyrightInfo()))
        if DB.termsOfService.getAgreedTime() == None:
            self.setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False)
            self.agreed.hide()
            self.agree.stateChanged.connect(self.checkAgree)
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
            self.buttonBox.accepted.connect(DB.termsOfService.agree)
            self.buttonBox.rejected.connect(App.exit)
        else:
            self.agree.hide()
            self.agreed.setText(T("#Agreed at {time}", time=str(DB.termsOfService.getAgreedTime()).split(".")[0]))
            self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Ok)

    def checkAgree(self):
        if self.agree.isChecked():
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)