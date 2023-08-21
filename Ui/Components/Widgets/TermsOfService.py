from Core.Ui import *
from Services.Document import DocumentData, DocumentButtonData
from Ui.DocumentView import DocumentView


class TermsOfService(DocumentView):
    termsOfServiceAccepted = QtCore.pyqtSignal()
    appShutdownRequested = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(DocumentData(title=T("terms-of-service"), content=Utils.getDocument("TermsOfService.txt", App.Translator.getLanguage()).format(appName=Config.APP_NAME)), parent=parent)
        if self.isEssential():
            self.setModal(True)
            okButton = self.addButton(
                DocumentButtonData(
                    text=T("ok"),
                    action=App.Preferences.setup.agreeTermsOfService,
                    role="accept",
                    default=True
                )
            )
            self.addButton(
                DocumentButtonData(
                    text=T("cancel"),
                    role="reject",
                    default=False
                )
            )
            okButton.setEnabled(False)
            self._ui.checkBox.toggled.connect(okButton.setEnabled)
            self._ui.checkBox.setText(T("#I accept the terms of service."))
            self._ui.buttonBox.accepted.connect(self.termsOfServiceAccepted)
            self._ui.buttonBox.rejected.connect(self.appShutdownRequested)
        else:
            self._ui.checkBox.setEnabled(False)
            self._ui.checkBox.setChecked(True)
            self._ui.checkBox.setText(T("#Agreed at {time}", time=App.Preferences.setup.getTermsOfServiceAgreement().toTimeZone(App.Preferences.localization.getTimezone()).toString("yyyy-MM-dd HH:mm:ss")))
            self.addButton(
                DocumentButtonData(
                    text=T("ok"),
                    role="accept",
                    default=True
                )
            )
        self._ui.checkBox.show()

    def isEssential(self) -> bool:
        return App.Preferences.setup.getTermsOfServiceAgreement() == None