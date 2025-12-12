from django.contrib import admin

from .models import Actualización
from .models import Aula
from .models import Ayudante
from .models import Carrera
from .models import Docente
from .models import Gestión
from .models import Grupo
from .models import Horario
from .models import Materia
from .models import NivelMateria


class GrupoAdmin(admin.ModelAdmin):
    list_display = ("código", "grupo", "materia", "actualización")
    list_filter = ("materia", "actualización")
    search_fields = ("código", "materia__nombre", "actualización__fecha")


class MateriaAdmin(admin.ModelAdmin):
    list_display = (
        "código",
        "nombre",
    )
    list_filter = ("código", "nivelmateria__carrera")
    search_fields = (
        "código",
        "nombre",
    )


class NivelMateriaAdmin(admin.ModelAdmin):
    list_display = ("código", "nivel", "materia", "carrera")
    list_filter = ("nivel", "carrera", "materia")
    search_fields = ("código", "nivel", "carrera__nombre", "materia__nombre")


class CarreraAdmin(admin.ModelAdmin):
    list_display = ("código", "nombre")
    list_filter = ("nombre",)
    search_fields = ("código", "nombre")


class DocenteAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    list_filter = ("nombre",)
    search_fields = ("nombre",)


class AyudanteAdmin(admin.ModelAdmin):
    list_display = ("nombre",)
    list_filter = ("nombre",)
    search_fields = ("nombre",)


class AulaAdmin(admin.ModelAdmin):
    list_display = ("código",)
    list_filter = ("código",)
    search_fields = ("código",)


class HorarioAdmin(admin.ModelAdmin):
    list_display = ("código", "día", "inicio", "aula", "grupo", "grupo__docente")
    list_filter = (
        "aula",
        "día",
        "inicio",
        "fin",
        "grupo__materia__nivelmateria__carrera",
        "grupo__materia",
        "grupo__docente",
        "grupo__ayudante",
    )
    search_fields = (
        "código",
        "nombre",
        "grupo__materia__nivelmateria__carrera__nombre",
    )


admin.site.register(Actualización)
admin.site.register(Gestión)
admin.site.register(Carrera, CarreraAdmin)
admin.site.register(Docente, DocenteAdmin)
admin.site.register(Ayudante, AyudanteAdmin)
admin.site.register(Materia, MateriaAdmin)
admin.site.register(NivelMateria, NivelMateriaAdmin)
admin.site.register(Aula, AulaAdmin)
admin.site.register(Grupo, GrupoAdmin)
admin.site.register(Horario, HorarioAdmin)
