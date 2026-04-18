"""
ophix_auth_oidc.urls
~~~~~~~~~~~~~~~~~~~~
Mounts the mozilla-django-oidc URL patterns at /oidc/.

Provides: /oidc/authenticate/, /oidc/callback/, /oidc/logout/

Only active when OIDC_ENABLED is True (i.e. OIDC_RP_CLIENT_ID is set and
mozilla-django-oidc is installed).
"""

from django.conf import settings
from django.urls import include, path

urlpatterns = []

if getattr(settings, "OIDC_ENABLED", False):
    urlpatterns += [path("oidc/", include("mozilla_django_oidc.urls"))]
