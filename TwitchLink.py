from Core.App import App
from Core.Ui import *

import os
import sys


def TwitchLink():
    exitCode = App.start(Ui.MainWindow())
    if exitCode == App.EXIT_CODE.RESTART:
        os.execl(sys.executable, *sys.argv)
    return exitCode

if __name__ == "__main__":
    sys.exit(TwitchLink())