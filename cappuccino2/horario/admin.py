from django.contrib import admin

from .models import Actualización
from .models import Aula
from .models import Ayudante
from .models import Carrera
from .models import Docente
from .models import Grupo
from .models import Horario
from .models import Materia
from .models import NivelMateria

admin.site.register(Actualización)
admin.site.register(Carrera)
admin.site.register(Docente)
admin.site.register(Ayudante)
admin.site.register(Materia)
admin.site.register(NivelMateria)
admin.site.register(Aula)
admin.site.register(Grupo)
admin.site.register(Horario)
