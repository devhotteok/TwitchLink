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
    def __init__(self, contentId=None, date=None, title="", content="", contentType="text", modal=False, blockable=False, buttons=None):
        self.contentId = contentId
        self.date = date
        self.title = title
        self.content = content
        self.contentType = contentType
        self.modal = modal
        self.blockable = blockable
        self.buttons = buttons or []