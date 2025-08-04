from Core.Ui import *
from Services.Script import Script
from Services.Document import DocumentData, DocumentButtonData

from PyQt6 import QtWebEngineCore


class DocumentViewButton(QtWidgets.QPushButton):
    def __init__(self, documentButtonData: DocumentButtonData, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.setText(documentButtonData.text)
        self._action = None if documentButtonData.action == None else Script(documentButtonData.action, parent=self)
        self._role = documentButtonData.role
        self.setDefault(documentButtonData.default)
        self.clicked.connect(self.runAction)

    def runAction(self) -> None:
        if self._action != None:
            self._action()

    def getRole(self) -> QtWidgets.QDialogButtonBox.ButtonRole:
        return self._role


class DocumentView(QtWidgets.QWidget):
    closeRequested = QtCore.pyqtSignal(object)

    def __init__(self, documentData: DocumentData, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.documentData = documentData
        self._ui = UiLoader.load("documentView", self)
        self.setTitle(documentData.title)
        self.setContent(documentData.content, documentData.contentType)
        self.setModal(documentData.modal)
        self.setBlockExpiration(False if documentData.contentId == None else documentData.blockExpiration)
        for button in documentData.buttons:
            self.addButton(button)
        self._ui.buttonBox.accepted.connect(self._requestClose)
        if self.isBlockable():
            self._ui.buttonBox.accepted.connect(self._checkContentBlock)
        self._ui.buttonBox.rejected.connect(self._requestClose)

    def setTitle(self, title: str) -> None:
        self.setWindowTitle(title)
        self._ui.windowTitleLabel.setText(title)

    def setContent(self, content: str, contentType: str) -> None:
        if contentType == "html":
            self._ui.contentBrowser = Utils.setPlaceholder(self._ui.contentBrowser, QtWebEngineWidgets.QWebEngineView(parent=self))
            self._ui.contentBrowser.setHtml(content)
            self._ui.contentBrowser.page().newWindowRequested.connect(self._browserWindowRequestHandler)
        elif contentType == "url":
            self._ui.contentBrowser = Utils.setPlaceholder(self._ui.contentBrowser, QtWebEngineWidgets.QWebEngineView(parent=self))
            self._ui.contentBrowser.load(QtCore.QUrl(content))
            self._ui.contentBrowser.page().newWindowRequested.connect(self._browserWindowRequestHandler)
        else:
            self._ui.contentBrowser.setText(content)

    def setModal(self, modal: bool) -> None:
        self.modal = modal

    def setBlockExpiration(self, blockExpiration: bool | int | None) -> None:
        self.blockExpiration = blockExpiration
        if self.isBlockable():
            if self.blockExpiration == None:
                self._ui.checkBox.setText(T("#Do not show this again."))
            else:
                self._ui.checkBox.setText(T("#Do not show this again for {blockExpiration} days.", blockExpiration=blockExpiration))
            self._ui.checkBox.show()
        else:
            self._ui.checkBox.hide()

    def addButton(self, documentButtonData: DocumentButtonData) -> DocumentViewButton:
        buttonWidget = DocumentViewButton(documentButtonData, parent=self)
        self._ui.buttonBox.addButton(buttonWidget, buttonWidget.getRole())
        return buttonWidget

    def isModal(self) -> bool:
        return self.modal

    def isBlockable(self) -> bool:
        return self.blockExpiration != False

    def accept(self) -> None:
        self._ui.buttonBox.accepted.emit()

    def reject(self) -> None:
        self._ui.buttonBox.rejected.emit()

    def _requestClose(self) -> None:
        self.closeRequested.emit(self)

    def _checkContentBlock(self) -> None:
        if self._ui.checkBox.isChecked():
            App.Notifications.block(self.documentData)

    def _browserWindowRequestHandler(self, request: QtWebEngineCore.QWebEngineNewWindowRequest) -> None:
        Utils.openUrl(request.requestedUrl())