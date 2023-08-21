from Core.Ui import *
from Services.Messages import Messages
from Search import Engine
from Search.Helper.SearchHelper import SearchHelper
from Search.SearchMode import SearchMode


class Search(QtWidgets.QDialog):
    searchCompleted = QtCore.pyqtSignal(object)

    SEARCH_MESSAGE = {
        SearchMode.Types.CHANNEL: "#Checking channel info",
        SearchMode.Types.VIDEO: "#Checking video info",
        SearchMode.Types.CLIP: "#Checking clip info",
        SearchMode.Types.URL: "#Checking URL",
        SearchMode.Types.UNKNOWN: "#Searching"
    }

    def __init__(self, mode: SearchMode, parent: QtWidgets.QWidget | None = None):
        super().__init__(parent=parent)
        self.mode = mode
        self._ui = UiLoader.load("search", self)
        self.setup()

    def setup(self) -> None:
        if self.mode.isChannel():
            self._ui.windowTitleLabel.setText(T("#Search by Channel ID"))
            self.showSearchExamples(
                SearchHelper.getChannelIdExamples()
            )
        elif self.mode.isVideo():
            self._ui.windowTitleLabel.setText(T("#Search by Video / Clip ID"))
            self.showSearchExamples(
                SearchHelper.getVideoIdExamples(),
                SearchHelper.getClipIdExamples()
            )
        elif self.mode.isUrl():
            self._ui.windowTitleLabel.setText(T("#Search by Channel / Video / Clip URL"))
            self.showSearchExamples(
                SearchHelper.getUrlExamples()
            )
        else:
            self._ui.windowTitleLabel.setText(T("#Enter your search term."))
            self.showSearchExamples(
                SearchHelper.getChannelIdExamples(),
                SearchHelper.getVideoIdExamples(),
                SearchHelper.getClipIdExamples(),
                SearchHelper.getUrlExamples()
            )
        if (self.mode.isChannel() or self.mode.isUnknown()) and len(App.Preferences.general.getBookmarks()) != 0:
            self.currentText = self._ui.queryComboBox.currentText
            self._ui.queryComboBox.addItems(App.Preferences.general.getBookmarks())
            self._ui.queryComboBox.currentTextChanged.connect(self.checkText)
            if self.mode.isUnknown():
                self._ui.queryComboBox.setCurrentIndex(-1)
        else:
            self.currentText = self._ui.query.text
            self._ui.query.textChanged.connect(self.checkText)
        self.showInputPage()

    def showInputPage(self) -> None:
        self._ui.queryArea.setCurrentIndex(1 if (self.mode.isChannel() or self.mode.isUnknown()) and len(App.Preferences.general.getBookmarks()) != 0 else 0)
        self.checkText()

    def showSearchExamples(self, *args: tuple[str, str]) -> None:
        for examples in args:
            for exampleType, exampleText in examples:
                self._ui.searchExampleArea.layout().addRow(f"{T(exampleType)}:", QtWidgets.QLabel(exampleText, parent=self))
        if self._ui.searchExampleArea.layout().rowCount() == 0:
            self._ui.searchHelperArea.hide()

    def getCurrentQuery(self) -> str:
        return self.currentText().strip().replace(" ", "")

    def checkText(self) -> None:
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(self.getCurrentQuery() != "")

    def accept(self) -> None:
        self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(False)
        query = self.getCurrentQuery()
        if self.mode.isVideo() or self.mode.isClip():
            self.mode.setMode(SearchMode.Types.VIDEO if query.isnumeric() else SearchMode.Types.CLIP)
        self._ui.searchProgress.setText(T(self.SEARCH_MESSAGE[self.mode.getMode()], ellipsis=True))
        self._ui.queryArea.setCurrentIndex(2)
        Engine.SearchEngine(
            mode=self.mode,
            query=query,
            searchExternalContent=App.Preferences.advanced.isSearchExternalContentEnabled(),
            parent=self
        ).finished.connect(self._processSearchResult)

    def _processSearchResult(self, searchEngine: Engine.SearchEngine) -> None:
        if searchEngine.getError() == None:
            self.searchCompleted.emit(searchEngine.getData())
            super().accept()
        else:
            self._ui.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            self.showInputPage()
            if isinstance(searchEngine.getError(), Engine.Exceptions.ChannelNotFound):
                Utils.info("no-results-found", "#Channel not found.", parent=self)
            elif isinstance(searchEngine.getError(), Engine.Exceptions.VideoNotFound):
                Utils.info("no-results-found", "#Video not found.", parent=self)
            elif isinstance(searchEngine.getError(), Engine.Exceptions.ClipNotFound):
                Utils.info("no-results-found", "#Clip not found.", parent=self)
            elif isinstance(searchEngine.getError(), Engine.Exceptions.InvalidURL):
                Utils.info("no-results-found", "#This URL is invalid.", parent=self)
            elif isinstance(searchEngine.getError(), Engine.Exceptions.NoResultsFound):
                Utils.info("no-results-found", "#No Results Found.", parent=self)
            else:
                Utils.info(*Messages.INFO.NETWORK_ERROR, parent=self)