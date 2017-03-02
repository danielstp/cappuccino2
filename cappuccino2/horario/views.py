from django.shortcuts import render
from django.views.generic import DetailView, ListView, RedirectView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

from cappuccino2.horario.models import Carrera, Materia
#from django.contrib.auth.models import Group

from rest_framework import viewsets
from cappuccino2.horario.serializers import CarreraSerializer, MateriaSerializer


class CarreraViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Carrera.objects.all().order_by('nombre')
    serializer_class = CarreraSerializer


class MateriaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Materia.objects.all()
    serializer_class = MateriaSerializer


class HorarioListView(LoginRequiredMixin, ListView):
    model = Carrera
    # These next two lines tell the view to index lookups by username
    slug_field = 'username'
    slug_url_kwarg = 'username'
