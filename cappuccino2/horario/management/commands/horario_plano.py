import re
from pathlib import Path

import pdftotext
from django.conf import settings
from django.core.management.base import BaseCommand

from cappuccino2.horario.models import Aula
from cappuccino2.horario.models import Grupo
from cappuccino2.horario.models import Horario
from cappuccino2.horario.models import Materia
from cappuccino2.horario.models import NivelMateria


class Command(BaseCommand):
    help = "Actualizar Horarios"

    patron_semestre = re.compile(
        r"^Horario de Clases por Plan de estudios\s+(?P<semestre>\d+\s+del\s+\d+)\s+"
        r"Facultad de Ciencias y Tecnología-UMSS$",
        re.IGNORECASE + re.MULTILINE,
    )
    patron_fecha = re.compile(
        r"Elaborado por el Centro de Procesamiento de Datos @JcGa - FCyT\s+Unica "
        r"impresión OFICIAL de horarios en la Facultad\s+(?P<fecha>\d{1,2}/\d{1,2}/"
        r"\d{1,4})",
        re.IGNORECASE + re.MULTILINE,
    )
    patron_nivel = re.compile(
        r"^Plan: (?P<carrera>[\w\s\.\(\)]+)\((?P<códigoCarrera>\d+)\)\s+Nivel de "
        r"Estudios:\s(?P<nivel>[A-L])$",
        re.IGNORECASE + re.MULTILINE,
    )
    # (*) SisMat, Nombre Materia, Grupo, Horario, Nombre del Docente
    #  ww⮤ Ayudantía, Práctica o Laboratorio
    #
    patron_horario = re.compile(
        r"^\(?(?P<ayudantía>\*?)\)?\s*(?P<códigoMateria>\d+)\s(?P<materia>[\w\s]+)\s+(?P<grupo>\w+)\s+(?P<día>LU|MA|MI|JU|VI|SA)\s+"
        r"(?P<horaInicioFin>\d{3,4}-\d{3,4})\((?P<aula>\d+[A-Z]?)\)\s+(?P<docente>[\s\w\.]+)$",
        re.IGNORECASE + re.MULTILINE,
    )

    def handle(self, *args, **options):
        self.obtener_archivos()
        self.procesar_horarios()

    def __init__(self):
        self.cola_pdfs = []

    def obtener_archivos(self):
        ruta_base = Path(f"{settings.STATIC_ROOT}/horarios/")
        for archivo in (
            x for x in ruta_base.iterdir() if x.is_file() if x.match("*.pdf")
        ):
            with open(archivo, "rb") as f:
                self.cola_pdfs.append((pdftotext.PDF(f, physical=True), archivo.stem))

    def procesar_horarios(self):
        for archivo_pdf in self.cola_pdfs:
            for página in archivo_pdf[0]:
                self.cosechar(página, archivo_pdf[1])

    def cosechar(self, página, nombre_archivo):
        print(f"procesando... {nombre_archivo} ...")
        semestre = Command.patron_semestre.search(página).groupdict()["semestre"]
        fecha = Command.patron_fecha.search(página).groupdict()["fecha"]
        nivel = Command.patron_nivel.search(página).groupdict()["nivel"]
        carrera = Command.patron_nivel.search(página).groupdict()["carrera"]
        código_carrera = Command.patron_nivel.search(página).groupdict()[
            "códigoCarrera"
        ]

        print(f"{semestre = }, {fecha = }, {carrera = }({código_carrera}), {nivel = }")
        for hora in Command.patron_horario.finditer(página):
            print(hora.groupdict())

    def crea(self, tipo, nombre):
        try:
            ayudante = tipo.objects.get(nombre=nombre)
        except tipo.DoesNotExist:
            ayudante = tipo.objects.create(nombre=nombre)
            ayudante.save()
        return ayudante

    def crea_materia(
        self,
        materia,
        docente,
        obj,
        código,
        grupo,
        aula,
        inicia,
        termina,
        día,
        nivel,
        carrera,
    ):
        try:
            mat = Materia.objects.get(nombre=materia)
        except Materia.DoesNotExist:
            mat = Materia.objects.create(nombre=materia, código=código)
            mat.save()
        código_grupo = código + "_" + grupo
        código_nivel_materia = str(carrera.código) + "_" + código
        try:
            nivel_materia = NivelMateria.objects.get(código=código_nivel_materia)
        except NivelMateria.DoesNotExist:
            nivel_materia = NivelMateria.objects.create(
                código=código_nivel_materia, materia=mat, carrera=carrera, nivel=nivel
            )
            nivel_materia.save()
        try:
            grup = Grupo.objects.get(código=código_grupo)
        except Grupo.DoesNotExist:
            grup = Grupo.objects.create(código=código_grupo, materia=mat)
            grup.grupo = grupo
            grup.save()
        if docente:
            grup.docente = obj
            grup.save()
        else:
            grup.ayudante = obj
            grup.save()
        try:
            aul = Aula.objects.get(código=aula)
        except Aula.DoesNotExist:
            aul = Aula.objects.create(código=aula)
            aul.save()
        ini_t = self.patronHora.findall(inicia)[0]
        ini = ini_t[0] + ":" + ini_t[1]
        fin_t = self.patronHora.findall(termina)[0]
        fin = fin_t[0] + ":" + fin_t[1]
        try:
            hora = Horario.objects.get(código=código_grupo + "_" + día)
        except Horario.DoesNotExist:
            hora = Horario.objects.create(
                código=código_grupo + "_" + día,
                grupo=grup,
                aula=aul,
                inicio=ini,
                fin=fin,
                día=día,
            )
            hora.save()
