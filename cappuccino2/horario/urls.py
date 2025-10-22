from django.urls import include
from django.urls import path
from rest_framework.routers import DefaultRouter

from cappuccino2.horario.views import ActualizaciónViewSet
from cappuccino2.horario.views import AulaViewSet
from cappuccino2.horario.views import AyudanteViewSet
from cappuccino2.horario.views import CarreraViewSet
from cappuccino2.horario.views import DocenteViewSet
from cappuccino2.horario.views import GrupoViewSet
from cappuccino2.horario.views import HorarioViewSet
from cappuccino2.horario.views import MateriaViewSet
from cappuccino2.horario.views import NivelMateriaViewSet

router = DefaultRouter()
router.register(r"carreras", CarreraViewSet)
router.register(r"materias", MateriaViewSet)
router.register(r"niveles-materias", NivelMateriaViewSet)
router.register(r"horarios", HorarioViewSet)
router.register(r"actualizaciones", ActualizaciónViewSet)
router.register(r"docentes", DocenteViewSet)
router.register(r"ayudantes", AyudanteViewSet)
router.register(r"aulas", AulaViewSet)
router.register(r"grupos", GrupoViewSet)

app_name = "horario"

urlpatterns = [
    path("", include(router.urls)),
]
