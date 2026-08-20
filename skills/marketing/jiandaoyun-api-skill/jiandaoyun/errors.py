"""Structured errors that are safe to return to an Agent."""


class JiandaoyunError(Exception):
    def __init__(self, error_type, message, *, code=None, retryable=False, details=None):
        super().__init__(message)
        self.error_type = error_type
        self.message = message
        self.code = code
        self.retryable = retryable
        self.details = details

    def as_dict(self):
        error = {
            "type": self.error_type,
            "message": self.message,
            "retryable": self.retryable,
        }
        if self.code is not None:
            error["code"] = self.code
        if self.details is not None:
            error["details"] = self.details
        return error
