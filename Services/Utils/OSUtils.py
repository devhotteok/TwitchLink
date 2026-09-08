from .OSAdapters.BaseAdapter import BaseAdapter
from .OSAdapters.Windows import WindowsUtils
from .OSAdapters.MacOS import MacOSUtils
from .OSAdapters.Linux import LinuxUtils


OSUtils: BaseAdapter
if BaseAdapter.isWindows():
    OSUtils = WindowsUtils
elif BaseAdapter.isMacOS():
    OSUtils = MacOSUtils
else:
    OSUtils = LinuxUtils