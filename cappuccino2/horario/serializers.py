from cappuccino2.horario.models import Carrera, Materia
#from django.contrib.auth.models import Group
from rest_framework import serializers


class CarreraSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Carrera
        fields = ('código', 'nombre')


class MateriaSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Materia
        fields = ('código', 'nombre')