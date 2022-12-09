from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    name = "celulas_responsaveis.users"
    verbose_name = _("Users")

    def ready(self):
        try:
            import celulas_responsaveis.users.signals  # noqa F401
        except ImportError:
            pass
