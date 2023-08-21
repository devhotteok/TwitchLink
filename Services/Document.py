from PyQt6 import QtWidgets

import typing


class DocumentButtonData:
    BUTTON_ROLES = {
        "accept": QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole,
        "reject": QtWidgets.QDialogButtonBox.ButtonRole.RejectRole,
        "action": QtWidgets.QDialogButtonBox.ButtonRole.ActionRole
    }

    def __init__(self, text: str = "", action: str | typing.Callable | None = None, role: str = "accept", default: bool = False):
        self.text = text
        self.action = action
        self.role = self.BUTTON_ROLES.get(role, QtWidgets.QDialogButtonBox.ButtonRole.AcceptRole)
        self.default = default


class DocumentData:
    def __init__(self, contentId: str | None = None, contentVersion: int | str = 0, title: str = "", content: str = "", contentType: str = "text", modal: bool = False, blockExpiration: bool | int | None = False, buttons: list[DocumentButtonData] | None = None):
        self.contentId = contentId
        self.contentVersion = contentVersion
        self.title = title
        self.content = content
        self.contentType = contentType
        self.modal = modal
        self.blockExpiration = blockExpiration
        self.buttons = buttons or []