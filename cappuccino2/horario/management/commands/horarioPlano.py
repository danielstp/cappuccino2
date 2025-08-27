import fileinput
import re
from pathlib import Path

import pdftotext
from django.conf import settings
from django.core.management.base import BaseCommand

from cappuccino2.horario.models import Aula, Ayudante, Carrera, Docente, Grupo, Horario, Materia, NivelMateria


class Command(BaseCommand):
    help = "Actualizar Horarios"

    patronSemestre = re.compile(
        r"^Horario de Clases por Plan de estudios\s+(?P<semestre>\d+\s+del\s+\d+)\s+Facultad de Ciencias y Tecnología-UMSS$",
        re.IGNORECASE + re.MULTILINE,
    )
    patronFecha = re.compile(
        r"Elaborado por el Centro de Procesamiento de Datos @JcGa - FCyT\s+Unica "
        r"impresión OFICIAL de horarios en la Facultad\s+(?P<fecha>\d{1,2}/\d{1,2}/\d{1,4})",
        re.IGNORECASE + re.MULTILINE,
    )
    patronNivel = re.compile(
        r"^Plan: (?P<carrera>[\w\s\.\(\)]+)\((?P<códigoCarrera>\d+)\)\s+Nivel de Estudios:\s(?P<nivel>[A-L])$",
        re.IGNORECASE + re.MULTILINE,
    )
    # (*) SisMat, Nombre Materia, Grupo, Horario, Nombre del Docente
    #  ww⮤ Ayudantía, Práctica o Laboratorio
    #
    patronHorario = re.compile(
        r"^\(?(?P<ayudantía>\*?)\)?\s*(?P<códigoMateria>\d+)\s(?P<materia>[\w\s]+)\s+(?P<grupo>\w+)\s+(?P<día>LU|MA|MI|JU|VI|SA)\s+"
        r"(?P<horaInicioFin>\d{3,4}-\d{3,4})\((?P<aula>\d+[A-Z]?)\)\s+(?P<docente>[\s\w\.]+)$",
        re.IGNORECASE + re.MULTILINE,
    )

    def handle(self, *args, **options):
        self.obtenerArchivos()
        self.procesarHorarios()

    def __init__(self):
        self.colaPDFs = list()

    def obtenerArchivos(self):
        rutaBase = Path(f"{settings.STATIC_ROOT}/horarios/")
        for archivo in (x for x in rutaBase.iterdir() if x.is_file() if x.match("*.pdf")):
            with open(archivo, "rb") as f:
                self.colaPDFs.append((pdftotext.PDF(f, physical=True), archivo.stem))

    def procesarHorarios(self):
        for archivoPDF in self.colaPDFs:
            for página in archivoPDF[0]:
                self.cosechar(página, archivoPDF[1])

    def cosechar(self, página, nombreArchivo):
        print(f"procesando... {nombreArchivo} ...")
        semestre = Command.patronSemestre.search(página).groupdict()["semestre"]
        fecha = Command.patronFecha.search(página).groupdict()["fecha"]
        nivel = Command.patronNivel.search(página).groupdict()["nivel"]
        carrera = Command.patronNivel.search(página).groupdict()["carrera"]
        códigoCarrera = Command.patronNivel.search(página).groupdict()["códigoCarrera"]

        print(f"semestre={semestre}, fecha={fecha}, carrera={carrera}({códigoCarrera}), nivel={nivel}")
        for hora in Command.patronHorario.finditer(página):
            print(hora.groupdict())

        # self.creaMateria(materia,True,self.crea(Docente, docente),código,grupo,aula,inicia,termina,día,nivel,objCarrera,)

    def crea(self, tipo, nombre):
        try:
            ayudante = tipo.objects.get(nombre=nombre)
        except tipo.DoesNotExist:
            ayudante = tipo.objects.create(nombre=nombre)
            ayudante.save()
        return ayudante

    def creaMateria(self, materia, docente, obj, código, grupo, aula, inicia, termina, día, nivel, carrera):
        try:
            mat = Materia.objects.get(nombre=materia)
        except Materia.DoesNotExist:
            mat = Materia.objects.create(nombre=materia, código=código)
            mat.save()
        codGrup = código + "_" + grupo
        codNivelMateria = str(carrera.código) + "_" + código
        try:
            nivelMateria = NivelMateria.objects.get(código=codNivelMateria)
        except NivelMateria.DoesNotExist:
            nivelMateria = NivelMateria.objects.create(
                código=codNivelMateria, materia=mat, carrera=carrera, nivel=nivel
            )
            nivelMateria.save()
        try:
            grup = Grupo.objects.get(código=codGrup)
        except Grupo.DoesNotExist:
            grup = Grupo.objects.create(código=codGrup, materia=mat)
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
            aul.save
        iniT = self.patronHora.findall(inicia)[0]
        ini = iniT[0] + ":" + iniT[1]
        finT = self.patronHora.findall(termina)[0]
        fin = finT[0] + ":" + finT[1]
        # ini = time.strptime(inicia, "%H%M")
        # fin = time.strptime(termina, "%H%M")
        try:
            hora = Horario.objects.get(código=codGrup + "_" + día)
        except Horario.DoesNotExist:
            hora = Horario.objects.create(
                código=codGrup + "_" + día, grupo=grup, aula=aul, inicio=ini, fin=fin, día=día
            )
            hora.save()
