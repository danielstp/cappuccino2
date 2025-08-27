from django.contrib import admin

from .models import Actualización, Aula, Ayudante, Carrera, Docente, Grupo, Horario, Materia, NivelMateria

admin.site.register(Actualización)
admin.site.register(Carrera)
admin.site.register(Docente)
admin.site.register(Ayudante)
admin.site.register(Materia)
admin.site.register(NivelMateria)
admin.site.register(Aula)
admin.site.register(Grupo)
admin.site.register(Horario)
