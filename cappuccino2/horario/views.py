from django.shortcuts import render
from django.views.generic import DetailView, ListView, RedirectView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

from cappuccino2.horario.models import ( Carrera, NivelMateria, Materia,
    Actualización, Docente, Ayudante, Aula, Grupo, Horario )
#from django.contrib.auth.models import Group

from rest_framework import viewsets
from cappuccino2.horario.serializers import ( CarreraSerializer,
    NivelMateriaSerializer, MateriaSerializer, ActualizaciónSerializer,
    DocenteSerializer, AyudanteSerializer, AulaSerializer, GrupoSerializer,
    HorarioSerializer)

class CarreraViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """
    queryset = Carrera.objects.all()
    serializer_class = CarreraSerializer
    filter_fields  = ('código','nombre','pdf','fecha','fechaPDF',)




class MateriaViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer


class NivelMateriaViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """
    queryset = NivelMateria.objects.all()
    serializer_class = NivelMateriaSerializer


class HorarioListView(LoginRequiredMixin, ListView):
    model = Carrera
    # These next two lines tell the view to index lookups by username
    slug_field = 'username'
    slug_url_kwarg = 'username'



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


class HorarioViewSet(viewsets.ModelViewSet):
    """
    API endpoint
    """
    queryset = Horario.objects.all()
    serializer_class = HorarioSerializer
    filter_fields  = ('código','día','inicio','fin','aula','grupo','grupo__materia')
