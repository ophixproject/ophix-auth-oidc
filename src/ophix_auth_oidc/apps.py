from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OphixAuthOidcConfig(AppConfig):
    name = "ophix_auth_oidc"
    verbose_name = _("Ophix OIDC Authentication")
    default_auto_field = "django.db.models.BigAutoField"
