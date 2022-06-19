from Core.Ui import *
from Services.Messages import Messages
from Search import Engine
from Search.Helper.SearchHelper import SearchHelper
from Search.Modes import SearchModes


class Search(QtWidgets.QDialog, UiFile.search):
    SEARCH_MESSAGE = {
        SearchModes.CHANNEL: "#Checking channel info",
        SearchModes.VIDEO: "#Checking video info",
        SearchModes.CLIP: "#Checking clip info",
        SearchModes.URL: "#Checking URL"
    }

    def __init__(self, mode, parent=None):
        super(Search, self).__init__(parent=parent)
        self.mode = mode
        self.setup()

    def setup(self):
        if self.mode.isChannel():
            self.window_title.setText(T("#Search by Channel ID"))
            self.showSearchHelper(SearchHelper.getChannelIdExamples())
            self.queryComboBox.addItems(DB.general.getBookmarks())
        elif self.mode.isVideo():
            self.window_title.setText(T("#Search by Video / Clip ID"))
            self.showSearchHelper(SearchHelper.getVideoClipIdExamples())
        else:
            self.window_title.setText(T("#Search by Channel / Video / Clip URL"))
            self.showSearchHelper(SearchHelper.getUrlExamples())
        if self.mode.isChannel() and len(DB.general.getBookmarks()) != 0:
            self.currentText = self.queryComboBox.currentText
            self.queryComboBox.currentTextChanged.connect(self.checkText)
        else:
            self.currentText = self.query.text
            self.query.textChanged.connect(self.checkText)
        self.searchThread = Utils.WorkerThread(parent=self)
        self.searchThread.resultSignal.connect(self.processSearchResult)
        self.showInputPage()

    def showInputPage(self):
        self.queryArea.setCurrentIndex(1 if self.mode.isChannel() and len(DB.general.getBookmarks()) != 0 else 0)
        self.checkText()

    def showSearchHelper(self, examples):
        if len(examples) == 0:
            self.searchHelperArea.hide()
        else:
            self.searchExample.setText("\n".join(examples))

    def getCurrentQuery(self):
        return self.currentText().replace(" ", "")

    def checkText(self):
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(self.getCurrentQuery() != "")

    def accept(self):
        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(False)
        query = self.getCurrentQuery()
        if self.mode.isVideo() or self.mode.isClip():
            self.mode.setMode(SearchModes.VIDEO if query.isnumeric() else SearchModes.CLIP)
        self.searchProgress.setText(T(self.SEARCH_MESSAGE[self.mode.getMode()], ellipsis=True))
        self.queryArea.setCurrentIndex(2)
        self.searchThread.setup(
            target=Engine.Search.Query,
            args=(self.mode, query),
            kwargs={"searchExternalContent": DB.advanced.isExternalContentUrlEnabled()},
        )
        self.searchThread.start()

    def processSearchResult(self, result):
        if result.success:
            super().accept(result.data)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
            self.showInputPage()
            if isinstance(result.error, Engine.Exceptions.InvalidURL):
                self.info("no-results-found", "#This URL is invalid.")
            elif isinstance(result.error, Engine.Exceptions.ChannelNotFound):
                self.info("no-results-found", "#Channel not found.")
            elif isinstance(result.error, Engine.Exceptions.VideoNotFound):
                self.info("no-results-found", "#Video not found.")
            elif isinstance(result.error, Engine.Exceptions.ClipNotFound):
                self.info("no-results-found", "#Clip not found.")
            else:
                self.info(*Messages.INFO.NETWORK_ERROR)