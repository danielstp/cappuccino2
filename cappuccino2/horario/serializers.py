from cappuccino2.horario.models import Carrera, NivelMateria, Materia
#from django.contrib.auth.models import Group
from rest_framework import serializers


class CarreraSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Carrera
        fields = ('código', 'nombre', 'pdf', 'fecha', 'fechaPDF')


class MateriaSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Materia
        fields = ('código', 'nombre')


class NivelMateriaSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = NivelMateria
        fields = ('código', 'carrera', 'materia')