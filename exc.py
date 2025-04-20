class ServiceException(ValueError):
    pass


class TokenNotProvidedException(BaseException):
    def __init__(self):
        super().__init__("⚠️  API Token Was Not Provided")
