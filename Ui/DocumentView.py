from Core.Ui import *
from Services.Script import Script


class DocumentViewButton(QtWidgets.QPushButton):
    def __init__(self, documentButton, parent=None):
        super(DocumentViewButton, self).__init__(parent=parent)
        self.setText(documentButton.text)
        self.setAction(documentButton.action)
        self.setRole(documentButton.role)
        self.setDefault(documentButton.default)
        self.clicked.connect(self.runAction)

    def setAction(self, action):
        self.action = action

    def runAction(self):
        if self.action != None:
            Script.run(self.action)

    def setRole(self, role):
        self.role = role

    def getRole(self):
        return self.role


class DocumentView(QtWidgets.QWidget, UiFile.documentView):
    closeRequested = QtCore.pyqtSignal(object)

    def __init__(self, document, parent=None):
        super(DocumentView, self).__init__(parent=parent)
        self.contentId = document.contentId
        self.date = document.date
        self.setTitle(document.title)
        self.setContent(document.content, document.contentType)
        self.setModal(document.modal)
        self.setBlockable(document.blockable)
        for button in document.buttons:
            self.addButton(button)
        self.buttonBox.accepted.connect(self.requestClose)
        self.buttonBox.rejected.connect(self.requestClose)

    def setTitle(self, title):
        self.setWindowTitle(title)
        self.window_title.setText(title)

    def setContent(self, content, contentType):
        if contentType == "html":
            self.contentBrowser.setHtml(content)
        elif contentType == "url":
            self.contentBrowser = Utils.setPlaceholder(self.contentBrowser, QtWebEngineWidgets.QWebEngineView(parent=self))
            self.contentBrowser.load(QtCore.QUrl(content))
        else:
            self.contentBrowser.setText(content)

    def setModal(self, modal):
        self.modal = modal

    def setBlockable(self, blockable):
        self.blockable = blockable
        if self.blockable:
            self.checkBox.show()
        else:
            self.checkBox.hide()

    def addButton(self, button):
        buttonWidget = DocumentViewButton(button, parent=self)
        self.buttonBox.addButton(buttonWidget, buttonWidget.getRole())
        return buttonWidget

    def isModal(self):
        return self.modal

    def isBlockable(self):
        return self.blockable

    def accept(self):
        self.buttonBox.accepted.emit()

    def reject(self):
        self.buttonBox.rejected.emit()

    def requestClose(self):
        self.closeRequested.emit(self)