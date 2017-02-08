from django.db import models

DÍA_SEMANA = (
    ('LU', 'LU'),
    ('MA', 'MA'),
    ('MI', 'MI'),
    ('JU', 'JU'),
    ('VI', 'VI'),
    ('SA', 'SA'),
    ('DO', 'DO'),
)

class Carrera(models.Model):
    codigo = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=255)
    pdf = models.URLField()
    fecha = models.DateTimeField(default='2016-01-01 00:00:00-04')
    fechaPDF = models.DateTimeField(default='2016-01-01 00:00:00-04')
    def __str__(self):
        return self.nombre

class Docente(models.Model):
    nombre = models.CharField(max_length=255)
    def __str__(self):
        return self.nombre

class Ayudante(models.Model):
    nombre = models.CharField(max_length=255)
    def __str__(self):
        return self.nombre

class Materia(models.Model):
    nombre = models.CharField(max_length=255)
    codigo = models.IntegerField(primary_key=True)
    def __str__(self):
        return self.nombre

class Aula(models.Model):
    codigo = models.CharField(max_length=25,primary_key=True)
    def __str__(self):
        return self.codigo


class Grupo(models.Model):
    codigo = models.CharField(max_length=25,primary_key=True)
    materia = models.ForeignKey(Materia)
    docente = models.ForeignKey(Docente,null=True)
    ayudante = models.ForeignKey(Ayudante,null=True)
    def __str__(self):
        return self.materia.nombre+' Grupo:'+self.codigo


class Horario(models.Model):
    codigo = models.CharField(max_length=25,primary_key=True)
    día = models.CharField(max_length=2,choices=DÍA_SEMANA)
    inicio = models.TimeField()
    fin = models.TimeField()
    aula = models.ForeignKey(Aula)
    grupo = models.ForeignKey(Grupo)
    def __str__(self):
        return self.grupo.materia.nombre+' Grupo:'+ self.codigo
