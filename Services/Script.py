from Services.Utils.Utils import Utils


class Exceptions:
    class UnknownAction(Exception):
        def __str__(self):
            return "Unknown Action"


class Script:
    @classmethod
    def run(cls, script, ignoreExceptions=True):
        try:
            if isinstance(script, str):
                try:
                    actionType, actionData = script.split(":", 1)
                    if actionType == "open":
                        Utils.openUrl(actionData)
                    else:
                        raise
                except:
                    raise Exceptions.UnknownAction
            else:
                script()
        except Exception as e:
            if not ignoreExceptions:
                raise e