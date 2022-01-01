class Info:
    DOWNLOAD_ALREADY_COMPLETED = ("notification", "#The download has already been completed.")
    FOLDER_NOT_FOUND = ("error", "#Folder not found.\nIt has been moved, renamed or deleted.")
    FILE_NOT_FOUND = ("error", "#File not found.\nIt has been moved, renamed or deleted.")
    FILE_SYSTEM_ERROR = ("system-error", "#A system error has occurred.\n\nPossible Causes\n\n* Too long or invalid filename or path\n* Out of storage capacity\n* Needs permission to perform this action\n\nIf the error persists, try Run as administrator.")
    NETWORK_ERROR = ("network-error", "#A network error has occurred.")
    DOWNLOAD_ERROR = ("error", "#An error occurred while downloading.")

    UNAVAILABLE_FILENAME_OR_DIRECTORY = ("error", "#The target directory or filename is unavailable.")

    SERVER_CONNECTION_FAILED = ("error", "#A temporary error occurred while connecting to the server.\nPlease try again later.")

    TEMPORARY_ERROR = ("error", "A temporary error has occurred.\nPlease try again later.")
    AUTHENTICATION_ERROR = ("authentication-error", "#An authentication error has occurred.\nIf the error persists, try logging in again.")
    LOGIN_EXPIRED = ("login-expired", "#Your login has expired.\nIf you do not log in again, the downloader will operate in a logged out state.")


class Ask:
    STOP_DOWNLOAD = ("stop-download", "#Are you sure you want to stop the download?")
    CANCEL_DOWNLOAD = ("cancel-download", "#Are you sure you want to cancel the download?")

    FILE_OVERWRITE = ("overwrite", "#A file with the same name already exists.\nOverwrite?")

    APP_EXIT = ("notification", "#Are you sure you want to exit?")
    APP_EXIT_WHILE_DOWNLOADING = ("warning", "#There is a download in progress.\nDo you want to cancel and exit?")


class Messages:
    ASK = Ask
    INFO = Info