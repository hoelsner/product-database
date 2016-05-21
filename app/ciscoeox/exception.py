class ConnectionFailedException(BaseException):
    """
    exception if no connection to the server can be established
    """
    pass


class AuthorizationFailedException(BaseException):
    """
    exception if the authorization failed
    """
    pass


class ClaimTokenFailedException(BaseException):
    """
    exception if the renew of the token failed (wrong credentials)
    """
    pass


class CredentialsNotFoundException(BaseException):
    """
    signals that there are no client credentials defined
    """
    pass


class InvalidClientCredentialsException(BaseException):
    """
    wrong client credentials, API access is not authorized
    """
    pass


class CannotSaveFileException(BaseException):
    """
    exception raised if a file operation fails
    """
    pass


class CiscoApiCallFailed(BaseException):
    """
    exception raised if an API call failed
    """
    pass
