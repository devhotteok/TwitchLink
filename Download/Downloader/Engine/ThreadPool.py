from .Config import Config

from Services.Threading.ThreadPool import ThreadPool


DownloadThreadPool = ThreadPool(Config.RECOMMENDED_THREAD_LIMIT)