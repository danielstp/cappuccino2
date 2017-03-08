from django.shortcuts import render
from django.views.generic import DetailView, ListView, RedirectView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

from cappuccino2.horario.models import Carrera, NivelMateria, Materia
#from django.contrib.auth.models import Group

from rest_framework import viewsets
from cappuccino2.horario.serializers import CarreraSerializer, NivelMateriaSerializer, MateriaSerializer


class CarreraViewSet(viewsets.ModelViewSet):
    """
    API endpoint 
    """
    queryset = Carrera.objects.all().order_by('nombre')
    serializer_class = CarreraSerializer


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
