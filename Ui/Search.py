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
        SearchModes.URL: "#Checking URL",
        SearchModes.UNKNOWN: "#Searching"
    }

    def __init__(self, mode, parent=None):
        super(Search, self).__init__(parent=parent)
        self.mode = mode
        self.setup()

    def setup(self):
        if self.mode.isChannel():
            self.windowTitleLabel.setText(T("#Search by Channel ID"))
            self.showSearchExamples(
                SearchHelper.getChannelIdExamples()
            )
        elif self.mode.isVideo():
            self.windowTitleLabel.setText(T("#Search by Video / Clip ID"))
            self.showSearchExamples(
                SearchHelper.getVideoIdExamples(),
                SearchHelper.getClipIdExamples()
            )
        elif self.mode.isUrl():
            self.windowTitleLabel.setText(T("#Search by Channel / Video / Clip URL"))
            self.showSearchExamples(
                SearchHelper.getUrlExamples()
            )
        else:
            self.windowTitleLabel.setText(T("#Enter your search term."))
            self.showSearchExamples(
                SearchHelper.getChannelIdExamples(),
                SearchHelper.getVideoIdExamples(),
                SearchHelper.getClipIdExamples(),
                SearchHelper.getUrlExamples()
            )
        if (self.mode.isChannel() or self.mode.isUnknown()) and len(DB.general.getBookmarks()) != 0:
            self.currentText = self.queryComboBox.currentText
            self.queryComboBox.addItems(DB.general.getBookmarks())
            self.queryComboBox.currentTextChanged.connect(self.checkText)
            if self.mode.isUnknown():
                self.queryComboBox.setCurrentIndex(-1)
        else:
            self.currentText = self.query.text
            self.query.textChanged.connect(self.checkText)
        self.searchThread = Utils.WorkerThread(parent=self)
        self.searchThread.resultSignal.connect(self.processSearchResult)
        self.showInputPage()

    def showInputPage(self):
        self.queryArea.setCurrentIndex(1 if (self.mode.isChannel() or self.mode.isUnknown()) and len(DB.general.getBookmarks()) != 0 else 0)
        self.checkText()

    def showSearchExamples(self, *args):
        for examples in args:
            for exampleType, exampleText in examples:
                self.searchExampleArea.layout().addRow(f"{T(exampleType)}:", QtWidgets.QLabel(exampleText, parent=self))
        if self.searchExampleArea.layout().rowCount() == 0:
            self.searchHelperArea.hide()

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
            kwargs={"searchExternalContent": DB.advanced.isSearchExternalContentEnabled()},
        )
        self.searchThread.start()

    def processSearchResult(self, result):
        if result.success:
            super().accept(result.data)
        else:
            self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setEnabled(True)
            self.showInputPage()
            if isinstance(result.error, Engine.Exceptions.ChannelNotFound):
                self.info("no-results-found", "#Channel not found.")
            elif isinstance(result.error, Engine.Exceptions.VideoNotFound):
                self.info("no-results-found", "#Video not found.")
            elif isinstance(result.error, Engine.Exceptions.ClipNotFound):
                self.info("no-results-found", "#Clip not found.")
            elif isinstance(result.error, Engine.Exceptions.InvalidURL):
                self.info("no-results-found", "#This URL is invalid.")
            elif isinstance(result.error, Engine.Exceptions.NoResultsFound):
                self.info("no-results-found", "#No Results Found.")
            else:
                self.info(*Messages.INFO.NETWORK_ERROR)