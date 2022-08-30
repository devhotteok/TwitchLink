from Core.App import App
from Core.Ui import *

import sys


def TwitchLink():
    while True:
        exitCode = App.start(Ui.MainWindow())
        if exitCode != App.EXIT_CODE.RESTART:
            return exitCode

if __name__ == "__main__":
    sys.exit(TwitchLink())