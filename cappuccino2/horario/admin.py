from django.contrib import admin

from .models import Aula, Ayudante, Carrera, Docente, Grupo, Horario, Materia

admin.site.register(Carrera)
admin.site.register(Docente)
admin.site.register(Ayudante)
admin.site.register(Materia)
admin.site.register(Aula)
admin.site.register(Grupo)
admin.site.register(Horario)
