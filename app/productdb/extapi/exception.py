class ConnectionFailedException(BaseException):
    """
    Exception raised if connection issues to external servers occur
    """
    pass


class AuthorizationFailedException(BaseException):
    """
    Exception raised if the authorization with an external service failed
    """
    pass


class ClaimTokenFailedException(BaseException):
    """
    Exception raised if the renew of a token failed (wrong credentials)
    """
    pass


class CredentialsNotFoundException(BaseException):
    """
    Signals that there are no Client credentials defined
    """
    pass


class InvalidClientCredentialsException(BaseException):
    """
    Wrong client credentials, API access is not authorized
    """
    pass


class CannotSaveFileException(BaseException):
    """
    Exception raised if a file operation fails
    """
    pass


class CiscoApiCallFailed(BaseException):
    """
    Exception raised if an API call failed
    """
    pass
