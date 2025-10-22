import contextlib

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class HorarioConfig(AppConfig):
    name = "cappuccino2.horario"
    verbose_name = _("Horario")

    def ready(self):
        with contextlib.suppress(ImportError):
            import cappuccino2.users.signals  # noqa: F401,PLC0415
