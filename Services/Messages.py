class Info:
    ACTION_PERFORM_ERROR = ("warning", "messages.#you_cannot_perform_this_action_now")
    FOLDER_NOT_FOUND = ("error", "errors.#folder_not_found_it_has_been_moved_rena")
    FILE_NOT_FOUND = ("error", "errors.#file_not_found_it_has_been_moved_rename")
    FILE_SYSTEM_ERROR = ("system-error", "errors.#a_system_error_has_occurred_possible_ca")
    NETWORK_ERROR = ("network-error", "errors.#a_network_error_has_occurred")
    TEMPORARY_ERROR = ("error", "errors.#a_temporary_error_has_occurred_please_t")

    AUTHENTICATION_ERROR = ("authentication-error", "errors.#an_authentication_error_has_occurred_if")
    SESSION_EXPIRED = ("session-expired", "messages.#your_session_has_expired_please_sign_ag")


class Ask:
    STOP_DOWNLOAD = ("stop-download", "prompts.#are_you_sure_you_want_stop_download")
    CANCEL_DOWNLOAD = ("cancel-download", "prompts.#are_you_sure_you_want_cancel_download")
    STOP_CANCEL_ALL_DOWNLOADS = ("warning", "prompts.#there_are_one_or_more_downloads_progres")


class Messages:
    ASK = Ask
    INFO = Info