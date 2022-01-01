from PyQt5 import QtCore


class ResizableGrid:
    def __init__(self, gridLayout):
        self.gridLayout = gridLayout
        self.widgets = []
        self.column = 1

    def setColumn(self, column):
        if self.column != column:
            self.column = column
            self.reloadLayout()

    def getColumn(self):
        return self.column

    def addWidget(self, widget):
        self.widgets.append(widget)
        self.showWidget(len(self.widgets) - 1)

    def showWidget(self, index):
        self.gridLayout.addWidget(self.widgets[index], index // self.column, index % self.column, alignment=QtCore.Qt.AlignCenter)

    def clearAll(self):
        self.widgets = []
        self.clearLayout()

    def reloadLayout(self):
        self.clearLayout()
        for index in range(len(self.widgets)):
            self.showWidget(index)

    def clearLayout(self):
        for index in range(self.gridLayout.count()):
            self.gridLayout.itemAt(0).widget().setParent(None)