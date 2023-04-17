# from django.contrib.auth.models import Group
from rest_framework import serializers

from cappuccino2.horario.models import (
    Actualización,
    Aula,
    Ayudante,
    Carrera,
    Docente,
    Grupo,
    Horario,
    Materia,
    NivelMateria,
)


class CarreraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrera
        fields = "__all__"


class MateriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Materia
        fields = "__all__"


class NivelMateriaSerializer(serializers.ModelSerializer):
    materiaNombre = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = NivelMateria
        fields = ("materia", "carrera", "nivel", "materiaNombre")


class ActualizaciónSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actualización
        fields = "__all__"


class DocenteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Docente
        fields = "__all__"


class AyudanteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ayudante
        fields = "__all__"


class AulaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Aula
        fields = "__all__"


class GrupoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Grupo
        fields = "__all__"


class HorarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Horario
        fields = "__all__"
