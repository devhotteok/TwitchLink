from PyQt6 import QtCore, QtWebEngineCore


class IntegrityWebPage(QtWebEngineCore.QWebEnginePage):
    def __init__(self, profile: QtWebEngineCore.QWebEngineProfile, parent: QtCore.QObject | None = None):
        super().__init__(profile, parent=parent)
        script = QtWebEngineCore.QWebEngineScript()
        script.setInjectionPoint(QtWebEngineCore.QWebEngineScript.InjectionPoint.DocumentCreation)
        script.setWorldId(QtWebEngineCore.QWebEngineScript.ScriptWorldId.MainWorld)
        script.setRunsOnSubFrames(True)
        script.setSourceCode(
            """
                (() => {
                    if (typeof PublicKeyCredential !== "undefined") {
                        PublicKeyCredential.isConditionalMediationAvailable = async () => false;
                    }
                    if (typeof CredentialsContainer === "undefined") {
                        return;
                    }
                    for (const method of ["get", "create"]) {
                        const original = CredentialsContainer.prototype[method];
                        CredentialsContainer.prototype[method] = function(options) {
                            if (options && options.publicKey !== undefined) {
                                return Promise.reject(new DOMException(
                                    "WebAuthn is disabled",
                                    "NotAllowedError"
                                ));
                            }
                            return original.apply(this, arguments);
                        };
                    }
                })();
            """
        )
        self.scripts().insert(script)