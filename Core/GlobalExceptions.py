class Exceptions:
    class NetworkError(Exception):
        def __str__(self):
            return "Network Error"

    class FileSystemError(Exception):
        def __str__(self):
            return "File System Error"