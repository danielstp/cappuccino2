from django.db import models

DÍA_SEMANA = (
    ('1', 'LU'),
    ('2', 'MA'),
    ('3', 'MI'),
    ('4', 'JU'),
    ('5', 'VI'),
    ('6', 'SA'),
    ('7', 'DO'),
)

class Carrera(models.Model):
    codigo = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=255)
    pdf = models.URLField()
    fecha = models.DateTimeField(default='2016-01-01 00:00:00-04')
    fechaPDF = models.DateTimeField(default='2016-01-01 00:00:00-04')

class Docente(models.Model):
    nombre = models.CharField(max_length=255)

class Ayudante(models.Model):
    nombre = models.CharField(max_length=255)

class Materia(models.Model):
    nombre = models.CharField(max_length=255)
    codigo = models.IntegerField(primary_key=True)

class Aula(models.Model):
    codigo = models.CharField(max_length=25,primary_key=True)


class Grupo(models.Model):
    codigo = models.CharField(max_length=25,primary_key=True)
    materia = models.ForeignKey(Materia)
    docente = models.ForeignKey(Docente,null=True)
    ayudante = models.ForeignKey(Ayudante,null=True)


class Horario(models.Model):
    codigo = models.CharField(max_length=25,primary_key=True)
    día = models.CharField(max_length=2,choices=DÍA_SEMANA)
    inicio = models.TimeField()
    fin = models.TimeField()
    aula = models.ForeignKey(Aula)
    grupo = models.ForeignKey(Grupo)
