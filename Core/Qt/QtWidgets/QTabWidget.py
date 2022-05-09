from PyQt5 import QtWidgets


class _QTabWidget(QtWidgets.QTabWidget):
    def __init__(self, *args, **kwargs):
        super(_QTabWidget, self).__init__(*args, **kwargs)
        self.setTabBar(QtWidgets.QTabBar(parent=self))
QtWidgets.QTabWidget = _QTabWidget