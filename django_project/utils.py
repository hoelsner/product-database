from django.core.cache import cache
from app.config import AppSettings


def login_required_if_login_only_mode(request):
    """
    Test if the login only mode is enabled. If this is the case, test if a user is authentication. If this is not the
    case, redirect to the login form.
    """
    login_only_mode = cache.get("LOGIN_ONLY_MODE_SETTING", None)

    if not login_only_mode:
        # key not in cache
        app_settings = AppSettings()
        app_settings.read_file()
        cache.set("LOGIN_ONLY_MODE_SETTING", app_settings.is_login_only_mode(), 15 * 60)

    if login_only_mode:
        if not request.user.is_authenticated():
            return True

    return False

