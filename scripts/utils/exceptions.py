"""
Description: Defines custom exception classes for handling specific error cases
in the application, providing structured error handling and reporting.
"""


class ServiceException(ValueError):
    pass


class TokenNotProvidedException(BaseException):
    def __init__(self):
        super().__init__("⚠️  API Token Was Not Provided")


class ModelNotProvidedException(BaseException):
    def __init__(self):
        super().__init__("⚠️  No local models was found in the 'local_models' directory")
