from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from rest_framework import viewsets

from cappuccino2.horario.models import Actualización
from cappuccino2.horario.models import Aula
from cappuccino2.horario.models import Ayudante
from cappuccino2.horario.models import Carrera
from cappuccino2.horario.models import Docente
from cappuccino2.horario.models import Grupo
from cappuccino2.horario.models import Horario
from cappuccino2.horario.models import Materia
from cappuccino2.horario.models import NivelMateria
from cappuccino2.horario.serializers import ActualizaciónSerializer
from cappuccino2.horario.serializers import AulaSerializer
from cappuccino2.horario.serializers import AyudanteSerializer
from cappuccino2.horario.serializers import CarreraSerializer
from cappuccino2.horario.serializers import DocenteSerializer
from cappuccino2.horario.serializers import GrupoSerializer
from cappuccino2.horario.serializers import HorarioSerializer
from cappuccino2.horario.serializers import MateriaSerializer
from cappuccino2.horario.serializers import NivelMateriaSerializer


class CarreraViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """

    queryset = Carrera.objects.all()
    serializer_class = CarreraSerializer
    filter_fields = (
        "código",
        "nombre",
        "pdf",
        "fecha",
        "fecha_pdf",
    )


class MateriaViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """

    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer
    filter_fields = (
        "código",
        "nombre",
    )


class NivelMateriaViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """

    queryset = NivelMateria.objects.all()
    serializer_class = NivelMateriaSerializer
    filter_fields = (
        "materia",
        "carrera",
        "materia__nombre",
        "carrera__nombre",
        "nivel",
    )


class HorarioListView(LoginRequiredMixin, ListView):
    model = Carrera
    # These next two lines tell the view to index lookups by username
    slug_field = "username"
    slug_url_kwarg = "username"


class ActualizaciónViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """

    queryset = Actualización.objects.all()
    serializer_class = ActualizaciónSerializer


class DocenteViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """

    queryset = Docente.objects.all()
    serializer_class = DocenteSerializer


class AyudanteViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """

    queryset = Ayudante.objects.all()
    serializer_class = AyudanteSerializer


class AulaViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """

    queryset = Aula.objects.all()
    serializer_class = AulaSerializer


class GrupoViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """

    queryset = Grupo.objects.all()
    serializer_class = GrupoSerializer
    filter_fields = ("código", "grupo", "materia", "docente", "ayudante")


class HorarioViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """

    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer
    filter_fields = (
        "código",
        "día",
        "inicio",
        "fin",
        "aula",
        "grupo",
        "grupo__materia",
    )
