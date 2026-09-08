from Core.Ui import *
from Services.Document import DocumentData, DocumentButtonData
from Ui.DocumentView import DocumentView


class TermsOfService(DocumentView):
    termsOfServiceAccepted = QtCore.pyqtSignal()
    appShutdownRequested = QtCore.pyqtSignal()

    def __init__(self, parent: QtWidgets.QWidget | None = None):
        super().__init__(DocumentData(title=T("terms-of-service"), content=Utils.getDocument("TermsOfService.txt", App.Translator.getCurrentLanguageCode()).format(appName=Config.APP_NAME)), parent=parent)
        self._okButton = None
        self._cancelButton = None
        if self.isEssential():
            self.setModal(True)
            self._okButton = self.addButton(
                DocumentButtonData(
                    text=T("ok"),
                    action=App.Preferences.setup.agreeTermsOfService,
                    role="accept",
                    default=True
                )
            )
            self._cancelButton = self.addButton(
                DocumentButtonData(
                    text=T("cancel"),
                    role="reject",
                    default=False
                )
            )
            self._okButton.setEnabled(False)
            self._ui.checkBox.toggled.connect(self._okButton.setEnabled)
            self._ui.checkBox.setText(T("messages.#i_accept_terms_service"))
            self._ui.buttonBox.accepted.connect(self.termsOfServiceAccepted)
            self._ui.buttonBox.rejected.connect(self.appShutdownRequested)
        else:
            self._ui.checkBox.setEnabled(False)
            self._ui.checkBox.setChecked(True)
            self._ui.checkBox.setText(T("messages.#agreed", time=App.Preferences.setup.getTermsOfServiceAgreement().toTimeZone(App.Preferences.localization.getTimezone()).toString("yyyy-MM-dd HH:mm:ss")))
            self._okButton = self.addButton(
                DocumentButtonData(
                    text=T("ok"),
                    role="accept",
                    default=True
                )
            )
        self._ui.checkBox.show()

    def retranslateDynamicUi(self) -> None:
        self.setTitle(T("terms-of-service"))
        self.setContent(Utils.getDocument("TermsOfService.txt", App.Translator.getCurrentLanguageCode()).format(appName=Config.APP_NAME), self.documentData.contentType)
        if self.isEssential():
            self._ui.checkBox.setText(T("messages.#i_accept_terms_service"))
        else:
            self._ui.checkBox.setText(T("messages.#agreed", time=App.Preferences.setup.getTermsOfServiceAgreement().toTimeZone(App.Preferences.localization.getTimezone()).toString("yyyy-MM-dd HH:mm:ss")))
        
        if self._okButton:
            self._okButton.setText(T("ok"))
        if self._cancelButton:
            self._cancelButton.setText(T("cancel"))

    def isEssential(self) -> bool:
        return App.Preferences.setup.getTermsOfServiceAgreement() == None