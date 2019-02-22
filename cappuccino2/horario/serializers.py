from cappuccino2.horario.models import ( Carrera, NivelMateria, Materia,
          Actualización, Docente, Ayudante, Aula, Grupo, Horario )

#from django.contrib.auth.models import Group
from rest_framework import serializers


class CarreraSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Carrera
        fields = ('__all__')


class MateriaSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Materia
        fields = ('__all__')


class NivelMateriaSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = NivelMateria
        fields = ('__all__')


class ActualizaciónSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Actualización
        fields = ('__all__')

class DocenteSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Docente
        fields = ('__all__')

class AyudanteSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Ayudante
        fields = ('__all__')

class AulaSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Aula
        fields = ('__all__')


class GrupoSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Grupo
        fields = ('__all__')

class HorarioSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = Horario
        fields = ('__all__')

