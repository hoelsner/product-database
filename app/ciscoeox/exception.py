class ConnectionFailedException(Exception):
    """
    exception if no connection to the server can be established
    """
    pass


class AuthorizationFailedException(Exception):
    """
    exception if the authorization failed
    """
    pass


class ClaimTokenFailedException(Exception):
    """
    exception if the renew of the token failed (wrong credentials)
    """
    pass


class CredentialsNotFoundException(Exception):
    """
    signals that there are no client credentials defined
    """
    pass


class InvalidClientCredentialsException(Exception):
    """
    wrong client credentials, API access is not authorized
    """
    pass


class CannotSaveFileException(Exception):
    """
    exception raised if a file operation fails
    """
    pass


class CiscoApiCallFailed(Exception):
    """
    exception raised if an API call failed
    """
    pass
