"""
ophix_auth_oidc.settings
~~~~~~~~~~~~~~~~~~~~~~~~
Plugin settings for OpenID Connect authentication.

Activated when OIDC_RP_CLIENT_ID is set in the environment.
Requires mozilla-django-oidc (bundled as a dependency of this package).

The plugin loader in ophix-server-base handles:
  INSTALLED_APPS             — adds mozilla_django_oidc
  AUTHENTICATION_BACKENDS_PREPEND — inserts OphixOIDCBackend before ModelBackend
  MIDDLEWARE_INSERT_AFTER    — inserts SessionRefresh after AuthenticationMiddleware
All other uppercase keys are applied as non-destructive defaults.
"""

import logging
import os

logger = logging.getLogger(__name__)


def _int_env(name, default):
    try:
        return int(os.getenv(name) or default)
    except (TypeError, ValueError):
        return default


OIDC_RP_CLIENT_ID = os.getenv("OIDC_RP_CLIENT_ID", "")
OIDC_ENABLED = bool(OIDC_RP_CLIENT_ID)

if OIDC_ENABLED:
    try:
        import mozilla_django_oidc  # noqa: F401

        # Pull mozilla_django_oidc into INSTALLED_APPS via the loader's
        # INSTALLED_APPS special-case handling.
        INSTALLED_APPS = ["mozilla_django_oidc"]

        # Insert SessionRefresh middleware after AuthenticationMiddleware.
        MIDDLEWARE_INSERT_AFTER = {
            "django.contrib.auth.middleware.AuthenticationMiddleware": [
                "mozilla_django_oidc.middleware.SessionRefresh"
            ]
        }

        # Prepend OphixOIDCBackend before ModelBackend.
        AUTHENTICATION_BACKENDS_PREPEND = [
            "ophix_auth_oidc.backend.OphixOIDCBackend"
        ]

        # Core OIDC settings
        OIDC_RP_CLIENT_SECRET = os.getenv("OIDC_RP_CLIENT_SECRET", "")
        OIDC_RP_SIGN_ALGO = os.getenv("OIDC_RP_SIGN_ALGO", "RS256")

        # Endpoint URLs — set directly, or use the Azure AD tenant shortcut.
        _azure_tenant = os.getenv("OIDC_AZURE_TENANT_ID", "")
        if _azure_tenant:
            _azure_base = f"https://login.microsoftonline.com/{_azure_tenant}/v2.0"
            OIDC_OP_AUTHORIZATION_ENDPOINT = os.getenv(
                "OIDC_OP_AUTHORIZATION_ENDPOINT",
                f"{_azure_base}/oauth2/v2.0/authorize",
            )
            OIDC_OP_TOKEN_ENDPOINT = os.getenv(
                "OIDC_OP_TOKEN_ENDPOINT",
                f"{_azure_base}/oauth2/v2.0/token",
            )
            OIDC_OP_USER_ENDPOINT = os.getenv(
                "OIDC_OP_USER_ENDPOINT",
                f"{_azure_base}/oidc/userinfo",
            )
            OIDC_OP_JWKS_ENDPOINT = os.getenv(
                "OIDC_OP_JWKS_ENDPOINT",
                f"https://login.microsoftonline.com/{_azure_tenant}/discovery/v2.0/keys",
            )
        else:
            OIDC_OP_AUTHORIZATION_ENDPOINT = os.getenv("OIDC_OP_AUTHORIZATION_ENDPOINT", "")
            OIDC_OP_TOKEN_ENDPOINT = os.getenv("OIDC_OP_TOKEN_ENDPOINT", "")
            OIDC_OP_USER_ENDPOINT = os.getenv("OIDC_OP_USER_ENDPOINT", "")
            OIDC_OP_JWKS_ENDPOINT = os.getenv("OIDC_OP_JWKS_ENDPOINT", "")

        # Scopes — include openid + profile + email.
        # For Azure AD group claims, no extra scope is needed — groups appear
        # in the ID token when the app registration is configured to emit them.
        OIDC_RP_SCOPES = os.getenv("OIDC_RP_SCOPES", "openid profile email")

        # Redirect back to the admin after login/logout.
        LOGIN_REDIRECT_URL = "/admin/"
        LOGOUT_REDIRECT_URL = "/admin/login/"

        # Session refresh — re-check token validity every N seconds.
        OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS = _int_env(
            "OIDC_RENEW_ID_TOKEN_EXPIRY_SECONDS", default=900
        )

        # Group-to-permission mapping (object ID strings from the IdP).
        OIDC_STAFF_GROUP_ID = os.getenv("OIDC_STAFF_GROUP_ID", "")
        OIDC_SUPERUSER_GROUP_ID = os.getenv("OIDC_SUPERUSER_GROUP_ID", "")

        # Tell mozilla-django-oidc to use our custom backend.
        OIDC_AUTHENTICATION_BACKEND = "ophix_auth_oidc.backend.OphixOIDCBackend"

    except ImportError:
        logger.warning(
            "OIDC_RP_CLIENT_ID is set but mozilla-django-oidc is not installed. "
            "Install ophix-auth-oidc to enable SSO. "
            "Falling back to Django built-in authentication."
        )
        OIDC_ENABLED = False
