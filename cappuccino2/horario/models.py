from django.db import models

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
    fecha = models.DateTimeField(default="2016-01-01 00:00:00-04")
    fechaPDF = models.DateTimeField(default="2016-01-01 00:00:00-04")

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ("nombre",)


class Actualización(models.Model):
    carrera = models.ForeignKey(Carrera, on_delete=models.PROTECT)
    fecha = models.DateTimeField(default="2016-01-01 00:00:00-04")
    fechaPDF = models.DateTimeField(default="2016-01-01 00:00:00-04")

    def __str__(self):
        return self.carrera.nombre + self.fecha

    class Meta:
        ordering = ("fecha",)


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
