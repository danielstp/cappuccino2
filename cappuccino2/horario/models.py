from datetime import datetime as dt

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch.dispatcher import receiver

DÍA_SEMANA = (
    ("LU", "LU"),
    ("MA", "MA"),
    ("MI", "MI"),
    ("JU", "JU"),
    ("VI", "VI"),
    ("SA", "SA"),
    ("DO", "DO"),
)


class Carrera(models.Model):
    código = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=255)
    pdf = models.URLField()

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ("nombre",)


class Actualización(models.Model):
    carrera = models.ForeignKey(Carrera, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    fechaPDF = models.DateField(auto_now_add=True)
    semestre = models.CharField(max_length=10, default="1")

    def __str__(self):
        return f"{self.carrera.nombre} - {self.fecha.year()} - semestre {self.semestre}"

    class Meta:
        ordering = ("fecha",)
        verbose_name_plural = "Actualizaciones"


@receiver(signal=pre_save, sender=Actualización)
def actualización_pre_save(instance, **kwargs):
    instance.id_timestamp = int(dt.now().timestamp())


class Docente(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ("nombre",)


class Ayudante(models.Model):
    nombre = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ("nombre",)


class Materia(models.Model):
    nombre = models.CharField(max_length=255)
    código = models.IntegerField(primary_key=True)

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ("nombre",)


class NivelMateria(models.Model):
    código = models.CharField(max_length=20, primary_key=True)
    carrera = models.ForeignKey(Carrera, on_delete=models.PROTECT)
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT)
    nivel = models.CharField(max_length=1)

    def __str__(self):
        return f"{self.nivel}-{self.materia}-{self.carrera}"

    class Meta:
        ordering = (
            "carrera",
            "nivel",
            "materia",
        )


class Aula(models.Model):
    código = models.CharField(max_length=25, primary_key=True)

    def __str__(self):
        return self.código

    class Meta:
        ordering = ("código",)


class Grupo(models.Model):
    código = models.CharField(max_length=25, primary_key=True)
    grupo = models.CharField(max_length=2)
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT)
    docente = models.ForeignKey(Docente, null=True, on_delete=models.PROTECT)
    ayudante = models.ForeignKey(Ayudante, null=True, on_delete=models.PROTECT)
    actualización = models.ForeignKey(Actualización, on_delete=models.PROTECT)

    def __str__(self):
        return self.materia.nombre + " Grupo:" + self.código

    class Meta:
        ordering = ("grupo",)


class Horario(models.Model):
    código = models.CharField(max_length=25, primary_key=True)
    día = models.CharField(max_length=2, choices=DÍA_SEMANA)
    inicio = models.TimeField()
    fin = models.TimeField()
    aula = models.ForeignKey(Aula, on_delete=models.PROTECT)
    grupo = models.ForeignKey(Grupo, on_delete=models.PROTECT)

    def __str__(self):
        return self.grupo.materia.nombre + " Grupo:" + self.código

    class Meta:
        ordering = ("grupo",)
