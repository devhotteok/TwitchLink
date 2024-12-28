from .OSAdapters.BaseAdapter import BaseAdapter
from .OSAdapters.Windows import WindowsUtils
from .OSAdapters.MacOS import MacOSUtils


OSUtils: BaseAdapter = WindowsUtils if BaseAdapter.isWindows() else MacOSUtils