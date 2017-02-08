from django.apps import AppConfig


class HorarioConfig(AppConfig):
    name = 'cappuccino2.horario'
    verbose_name = "Horarios"

    def ready(self):
        """Override this to put in:
        """
        pass
