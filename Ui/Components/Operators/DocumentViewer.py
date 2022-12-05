from Core.Ui import *
from Ui.Components.Operators.TabManager import TabManager


class DocumentViewer(TabManager):
    def __init__(self, parent=None):
        super(DocumentViewer, self).__init__(parent=parent)
        self.modals = []
        self.setModal(False)
        self.tabCountChanged.connect(self.reloadState)

    def reloadState(self):
        if self.isModal():
            self.setTabEnabled(0, True)
            for index in range(1, self.count()):
                self.setTabEnabled(index, False)
        else:
            for index in range(self.count()):
                self.setTabEnabled(index, True)

    def setCurrentIndex(self, index):
        if not self.isModal():
            super().setCurrentIndex(index)

    def setCurrentWidget(self, widget):
        if not self.isModal():
            super().setCurrentWidget(widget)

    def showDocument(self, documentView, icon=None, uniqueValue=None, important=False):
        if documentView.isModal():
            self.setModal(True)
            self.setCurrentIndex(self.addTab(documentView, index=0 if important else len(self.modals), icon=icon or Icons.ANNOUNCEMENT_ICON, closable=False, uniqueValue=uniqueValue))
            self.modals.append(documentView)
        else:
            self.setCurrentIndex(self.addTab(documentView, index=len(self.modals) if important else -1, icon=icon or Icons.TEXT_FILE_ICON, uniqueValue=uniqueValue))
        documentView.closeRequested.connect(self.closeDocument)

    def closeDocument(self, documentView):
        if documentView.isModal():
            self.modals.remove(documentView)
            if len(self.modals) == 0:
                self.setModal(False)
        super().closeTab(self.indexOf(documentView))

    def closeTab(self, index):
        widget = self.widget(index)
        if isinstance(widget, Ui.DocumentView):
            widget.reject()
        else:
            super().closeTab(index)

    def setModal(self, modal):
        self.modal = modal
        self.setMovable(not modal)

    def isModal(self):
        return self.modal