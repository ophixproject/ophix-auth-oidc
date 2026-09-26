"""Minimal Django settings for running ophix_auth_oidc's test suite.

Deliberately does not depend on ophix-server-base - OphixOIDCBackend only
imports Django and mozilla-django-oidc directly, so the test settings only
need enough for the Django auth app + a User model to exist.
"""

SECRET_KEY = "test-secret-key-not-for-real-use"

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

USE_TZ = True

# mozilla-django-oidc's OIDCAuthenticationBackend.__init__ reads these
# unconditionally - placeholders are fine, no test here makes a real network
# call (get_userinfo's parent method is mocked out).
OIDC_OP_TOKEN_ENDPOINT = "https://example.com/token"
OIDC_OP_USER_ENDPOINT = "https://example.com/userinfo"
OIDC_RP_CLIENT_ID = "test-client-id"
OIDC_RP_CLIENT_SECRET = "test-client-secret"

# Group-to-permission mapping - overridden per-test via override_settings.
OIDC_STAFF_GROUP_ID = ""
OIDC_SUPERUSER_GROUP_ID = ""
