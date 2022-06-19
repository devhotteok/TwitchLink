from PyQt5 import QtWidgets


class DocumentButtonData:
    BUTTON_ROLES = {
        "accept": QtWidgets.QDialogButtonBox.AcceptRole,
        "reject": QtWidgets.QDialogButtonBox.RejectRole,
        "action": QtWidgets.QDialogButtonBox.ActionRole
    }

    def __init__(self, text="", action=None, role="accept", default=False):
        self.text = text
        self.action = action
        self.role = self.BUTTON_ROLES[role]
        self.default = default


class DocumentData:
    def __init__(self, contentId=None, contentVersion=0, title="", content="", contentType="text", modal=False, blockExpiry=False, buttons=None):
        self.contentId = contentId
        self.contentVersion = contentVersion
        self.title = title
        self.content = content
        self.contentType = contentType
        self.modal = modal
        self.blockExpiry = blockExpiry
        self.buttons = buttons or []