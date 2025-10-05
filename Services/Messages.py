class Info:
    ACTION_PERFORM_ERROR = ("warning", "#You cannot perform this action now.")
    FOLDER_NOT_FOUND = ("error", "#Folder not found.\nIt has been moved, renamed or deleted.")
    FILE_NOT_FOUND = ("error", "#File not found.\nIt has been moved, renamed or deleted.")
    FILE_SYSTEM_ERROR = ("system-error", "#A system error has occurred.\n\nPossible Causes\n\n* Too long or invalid filename or path\n* Out of storage capacity\n* Needs permission to perform this action\n\nIf the error persists, try Run as administrator.")
    NETWORK_ERROR = ("network-error", "#A network error has occurred.")
    TEMPORARY_ERROR = ("error", "#A temporary error has occurred.\nPlease try again later.")

    AUTHENTICATION_ERROR = ("authentication-error", "#An authentication error has occurred.\nIf the error persists, try signing in again.")
    SESSION_EXPIRED = ("session-expired", "#Your session has expired.\nPlease sign in again.")


class Ask:
    STOP_DOWNLOAD = ("stop-download", "#Are you sure you want to stop the download?")
    CANCEL_DOWNLOAD = ("cancel-download", "#Are you sure you want to cancel the download?")
    STOP_CANCEL_ALL_DOWNLOADS = ("warning", "#There are one or more downloads in progress.\nAre you sure you want to stop/cancel them all?")


class Messages:
    ASK = Ask
    INFO = Info