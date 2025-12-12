import logging
from datetime import datetime as dt
from datetime import timedelta

from django.db import models
from django.utils.timezone import get_default_timezone
from django.core.management.base import BaseCommand
from django.conf import settings

# Configure structured logging
logger = logging.getLogger(__name__)


# Define ANSI color codes as constants for easier use
class Color:
    PURPLE = "\033[95m"
    CYAN = "\033[96m"
    DARKCYAN = "\033[36m"
    BLUE = "\033[94m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    END = "\033[0m"  # Resets color to default


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

    class Meta:
        ordering = ("nombre",)
        indexes = [models.Index(fields=["nombre"])]

    def __str__(self):
        return self.nombre


class Gestión(models.Model):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    año = models.IntegerField()
    semestre = models.CharField(max_length=1)
    inicio = models.DateField()
    fin = models.DateField()

    class Meta:
        ordering = ("año", "semestre")
        indexes = [
            models.Index(fields=["año"]),
            models.Index(fields=["semestre"]),
        ]
        unique_together = ("año", "semestre")
        verbose_name_plural = "Gestiones"

    def __str__(self):
        return f"{self.año}.{self.semestre}"

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = f"{self.año}.{self.semestre}"
        super().save(*args, **kwargs)


class Actualización(models.Model):
    id = models.CharField(max_length=20, primary_key=True, editable=False)
    fecha = models.DateTimeField()
    fecha_pdf = models.DateField(null=True)
    url_pdf = models.URLField(max_length=255, default="")
    gestión = models.ForeignKey(Gestión, on_delete=models.PROTECT)
    carreras = models.ManyToManyField(Carrera)

    class Meta:
        unique_together = ("gestión", "fecha")
        ordering = ("fecha",)
        verbose_name_plural = "Actualizaciones"
        indexes = [
            models.Index(fields=["fecha"]),
            models.Index(fields=["fecha_pdf"]),
            models.Index(fields=["gestión"]),
            models.Index(fields=["gestión", "fecha"]),
        ]

    def __str__(self):
        return self.genera_id()

    def save(self, *args, **kwargs):
        if not self.id:
            self.id = self.genera_id()
        super().save(*args, **kwargs)

    def genera_id(self):
        return Actualización.genera_pk(self.gestión, self.fecha)

    @classmethod
    def genera_pk(cls, gestion: Gestión, fecha: dt):
        return f"{gestion}.{fecha.strftime('%m.%d.%H%M%Z')}"

    @classmethod
    def get_default_actualizacion(cls):
        return cls.objects.latest("fecha").pk


class Docente(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ("nombre",)
        indexes = [models.Index(fields=["nombre"])]

    def __str__(self):
        return self.nombre


class Ayudante(models.Model):
    nombre = models.CharField(max_length=255, unique=True)

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
        return self.genera_id()

    def save(self, *args, **kwargs):
        if not self.código:
            self.código = self.genera_id()
        super().save(*args, **kwargs)

    def genera_id(self):
        return NivelMateria.genera_pk(
            self.nivel,
            self.materia.código,
            self.carrera.código,
        )

    @classmethod
    def genera_pk(cls, nivel: str, materia: int, carrera: int):
        return f"{nivel}-{materia}-{carrera}"


class Aula(models.Model):
    código = models.CharField(max_length=25, primary_key=True)

    class Meta:
        ordering = ("código",)
        indexes = [models.Index(fields=["código"])]

    def __str__(self):
        return self.código


class Grupo(models.Model):
    código = models.CharField(max_length=32, primary_key=True, editable=False)
    grupo = models.CharField(max_length=2)
    materia = models.ForeignKey(Materia, on_delete=models.PROTECT)
    docente = models.ForeignKey(
        Docente,
        blank=True,
        null=True,
        default=None,
        on_delete=models.PROTECT,
    )
    ayudante = models.ForeignKey(
        Ayudante,
        blank=True,
        null=True,
        default=None,
        on_delete=models.PROTECT,
    )
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
        return f"{self.código}"

    def save(self, *args, **kwargs):
        if not self.código:
            if settings.DEBUG:
                print(Color.YELLOW + "Generando código")
                print(Color.BLUE + f"Grupo: {self.grupo}")
                print(Color.DARKCYAN + f"Materia: {self.materia}")
                print(Color.CYAN + f"Actualización: {self.actualización}")
                print(Color.RED + f"Generando ID: {self.genera_id()}" + Color.END)
            self.código = self.genera_id()
        super().save(*args, **kwargs)

    def genera_id(self):
        return Grupo.genera_pk(
            self.grupo,
            self.materia,
            self.actualización,
        )

    @classmethod
    def genera_pk(cls, grupo: str, materia: Materia, actualización: Actualización):
        return f"{grupo}-{materia.código}-{actualización}"


class Horario(models.Model):
    código = models.CharField(max_length=45, primary_key=True)
    día = models.CharField(max_length=2, choices=DÍA_SEMANA)
    inicio = models.TimeField()
    fin = models.TimeField()
    aula = models.ForeignKey(Aula, on_delete=models.PROTECT)
    grupo = models.ForeignKey(Grupo, on_delete=models.PROTECT)

    class Meta:
        ordering = ("grupo", "aula", "día", "inicio", "fin")
        indexes = [
            models.Index(fields=["código"]),
            models.Index(fields=["día"]),
            models.Index(fields=["aula"]),
            models.Index(fields=["grupo"]),
            models.Index(fields=["día", "aula"]),
            models.Index(fields=["día", "grupo"]),
            models.Index(fields=["día", "aula", "grupo"]),
            models.Index(fields=["día", "aula", "grupo", "inicio"]),
            models.Index(fields=["día", "aula", "grupo", "fin"]),
        ]

    def __str__(self):
        return self.genera_id()

    def save(self, *args, **kwargs):
        if not self.código:
            self.código = self.genera_id()
        super().save(*args, **kwargs)

    def genera_id(self):
        id = f"{self.día}-{self.inicio.strftime('%H%M')}-{self.grupo.código}"
        print(f"{Color.YELLOW}{Color.BOLD}{id = }{Color.END}")
        return id
