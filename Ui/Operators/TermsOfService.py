from Core.Ui import *
from Services.Document import DocumentData, DocumentButtonData
from Ui.DocumentView import DocumentView


class TermsOfService(DocumentView):
    termsOfServiceAccepted = QtCore.pyqtSignal()
    appShutdownRequested = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super(TermsOfService, self).__init__(DocumentData(title=T("terms-of-service"), content=Utils.getDoc("TermsOfService.txt", DB.localization.getLanguage(), appName=Config.APP_NAME)), parent=parent)
        if DB.setup.getTermsOfServiceAgreement() == None:
            self.setModal(True)
            okButton = self.addButton(
                DocumentButtonData(
                    text=T("ok"),
                    action=DB.setup.agreeTermsOfService,
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
            self.checkBox.toggled.connect(okButton.setEnabled)
            self.checkBox.setText(T("#I accept the terms of service."))
            self.buttonBox.accepted.connect(self.termsOfServiceAccepted)
            self.buttonBox.rejected.connect(self.appShutdownRequested)
        else:
            self.checkBox.setEnabled(False)
            self.checkBox.setChecked(True)
            self.checkBox.setText(T("#Agreed at {time}", time=DB.setup.getTermsOfServiceAgreement().strftime("%Y-%m-%d %H:%M:%S")))
            self.addButton(
                DocumentButtonData(
                    text=T("ok"),
                    role="accept",
                    default=True
                )
            )
        self.checkBox.show()