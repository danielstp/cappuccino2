from datetime import datetime as dt
from datetime import timedelta

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch.dispatcher import receiver
from django.utils.timezone import get_default_timezone
from django.utils.timezone import make_aware
from django.utils.timezone import now

LUNES = dt(2024, 12, 23, 0, 0, 0, tzinfo=get_default_timezone())

DÍA_SEMANA = (
    ("LU", LUNES.strftime("%A")),
    ("MA", (LUNES + timedelta(days=1)).strftime("%A")),
    ("MI", (LUNES + timedelta(days=2)).strftime("%A")),
    ("JU", (LUNES + timedelta(days=3)).strftime("%A")),
    ("VI", (LUNES + timedelta(days=4)).strftime("%A")),
    ("SA", (LUNES + timedelta(days=5)).strftime("%A")),
    ("DO", (LUNES + timedelta(days=6)).strftime("%A")),
)


class Carrera(models.Model):
    """
    Represents an academic program or career.

    Attributes:
        código (int): Primary key representing the unique code of the career.
        nombre (str): Name of the career.
        pdf (str): URL to a PDF document related to the career.

    Meta:
        ordering: Orders Carrera instances by 'nombre'.
        indexes: Adds a database index on the 'nombre' field.

    Methods:
        __str__: Returns the name of the career as its string representation.
    """

    código = models.IntegerField(primary_key=True)
    nombre = models.CharField(max_length=255)

    def fecha(self) -> dt:
        try:
            return Actualización.objects.filter(carrera=self).latest("fecha").fecha
        except Actualización.DoesNotExist:
            return make_aware(dt(2020, 1, 1, tzinfo=get_default_timezone()))

    def set_fecha(self, fecha: dt, fecha_pdf: dt, semestre: str):
        Actualización.objects.create(
            carrera=self,
            fecha=fecha,
            semestre=semestre,
            fecha_pdf=fecha_pdf,
        )

    def fecha_pdf(self) -> dt:
        try:
            return (
                Actualización.objects.filter(carrera=self).latest("fecha_pdf").fecha_pdf
            )
        except Actualización.DoesNotExist:
            return make_aware(dt(2020, 1, 1, tzinfo=get_default_timezone()))

    class Meta:
        ordering = ("nombre",)
        indexes = [models.Index(fields=["nombre"])]

    def __str__(self):
        return self.nombre


class Actualización(models.Model):
    carrera = models.ForeignKey(Carrera, on_delete=models.PROTECT)
    fecha = models.DateTimeField(auto_now_add=True)
    fecha_pdf = models.DateField(auto_now_add=True)
    url_pdf = models.URLField(max_length=255, default="")
    semestre = models.CharField(max_length=1, default="1")
    año = models.IntegerField(default=2020)

    class Meta:
        ordering = ("fecha",)
        verbose_name_plural = "Actualizaciones"
        indexes = [
            models.Index(fields=["fecha"]),
            models.Index(fields=["fecha_pdf"]),
            models.Index(fields=["semestre"]),
        ]

    def __str__(self):
        return f"{self.carrera.nombre} - {self.año} - semestre {self.semestre} - {self.fecha}"

    @classmethod
    def get_default_actualizacion(cls):
        return cls.objects.latest("fecha").id


@receiver(signal=pre_save, sender=Actualización)
def actualización_pre_save(instance, **kwargs):
    instance.id_timestamp = int(now().timestamp())


class Docente(models.Model):
    nombre = models.CharField(max_length=255)

    class Meta:
        ordering = ("nombre",)
        indexes = [models.Index(fields=["nombre"])]

    def __str__(self):
        return self.nombre


class Ayudante(models.Model):
    nombre = models.CharField(max_length=255)

    class Meta:
        ordering = ("nombre",)
        indexes = [models.Index(fields=["nombre"])]

    def __str__(self):
        return self.nombre


class Materia(models.Model):
    nombre = models.CharField(max_length=255)
    código = models.IntegerField(primary_key=True)

    class Meta:
        ordering = ("nombre",)
        indexes = [models.Index(fields=["nombre"])]

    def __str__(self):
        return self.nombre


class NivelMateria(models.Model):
    código = models.CharField(max_length=20, primary_key=True)
    carrera = models.ForeignKey(Carrera, on_delete=models.PROTECT)
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT)
    nivel = models.CharField(max_length=1)

    class Meta:
        ordering = (
            "carrera",
            "nivel",
            "materia",
        )
        indexes = [
            models.Index(fields=["código"]),
            models.Index(fields=["carrera"]),
            models.Index(fields=["nivel"]),
            models.Index(fields=["materia"]),
            models.Index(fields=["carrera", "nivel", "materia"]),
        ]

    def __str__(self):
        return f"{self.nivel}-{self.materia}-{self.carrera}"


class Aula(models.Model):
    código = models.CharField(max_length=25, primary_key=True)

    class Meta:
        ordering = ("código",)
        indexes = [models.Index(fields=["código"])]

    def __str__(self):
        return self.código


class Grupo(models.Model):
    código = models.CharField(max_length=25, primary_key=True)
    grupo = models.CharField(max_length=2)
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT)
    docente = models.ForeignKey(Docente, null=True, on_delete=models.PROTECT)
    ayudante = models.ForeignKey(Ayudante, null=True, on_delete=models.PROTECT)
    actualización = models.ForeignKey(Actualización, on_delete=models.PROTECT)

    class Meta:
        ordering = ("grupo",)
        indexes = [
            models.Index(fields=["código"]),
            models.Index(fields=["grupo"]),
            models.Index(fields=["materia"]),
            models.Index(fields=["docente"]),
            models.Index(fields=["ayudante"]),
            models.Index(fields=["actualización"]),
        ]

    def __str__(self):
        return f"{self.materia.nombre} Grupo:{self.código}"


class Horario(models.Model):
    código = models.CharField(max_length=25, primary_key=True)
    día = models.CharField(max_length=2, choices=DÍA_SEMANA)
    inicio = models.TimeField()
    fin = models.TimeField()
    aula = models.ForeignKey(Aula, on_delete=models.PROTECT)
    grupo = models.ForeignKey(Grupo, on_delete=models.PROTECT)

    class Meta:
        ordering = ("grupo",)
        indexes = [
            models.Index(fields=["código"]),
            models.Index(fields=["día"]),
            models.Index(fields=["inicio"]),
            models.Index(fields=["fin"]),
            models.Index(fields=["aula"]),
            models.Index(fields=["grupo"]),
        ]

    def __str__(self):
        return self.grupo.materia.nombre + " Grupo:" + self.código
