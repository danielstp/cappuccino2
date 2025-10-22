import datetime
import fileinput
import re
import subprocess
import urllib.request
from pathlib import Path

import pycurl
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from parsel import Selector

from cappuccino2.horario.models import Aula
from cappuccino2.horario.models import Ayudante
from cappuccino2.horario.models import Carrera
from cappuccino2.horario.models import Docente
from cappuccino2.horario.models import Grupo
from cappuccino2.horario.models import Horario
from cappuccino2.horario.models import Materia
from cappuccino2.horario.models import NivelMateria


class Command(BaseCommand):
    help = "Actualizar Horarios"

    patron_código = re.compile(r"^(\d+)\s+(.*)$")
    patron_nivel = re.compile(r"^Plan:[\s\d\w\(\)]+Nivel de Estudios:\s*([A-J])$")
    patron_hora = re.compile(r"(\d{1,2})(\d{2})$")
    patron_fecha = "%H:%M %d-%m-%Y"
    patron_fecha_apache = "%a, %d %b %Y %H:%M:%S %Z"

    def handle(self, *args, **options):
        self.descargar_horarios()
        self.generar_textos()
        self.procesar_horarios()

    def descargar_horarios(self, *args, **options):
        url = "http://fcyt.umss.edu.bo/horarios/"
        text = requests.get(url, timeout=settings.TIMEOUT).text
        selector = Selector(text=text)
        carreras = selector.xpath(
            "/html/body/table[4]//tr/td[3]/table//tr[2]/td/table//tr/td/table//tr/td[2]/div/font/text()",
        ).extract()
        fechas = selector.xpath(
            "/html/body/table[4]//tr/td[3]/table//tr[2]/td/table//tr/td/table//tr/td[4]/div/font/text()",
        ).extract()
        horarios_pdf = selector.xpath(
            "/html/body/table[4]//tr/td[3]/table//tr[2]/td/table//tr/td/table//tr/td[3]/div/font/a/@href",
        ).extract()
        código = {}
        for i, carrera_str in enumerate(carreras):
            tupla = self.patron_código.findall(carrera_str)
            if tupla:
                carrera_code = tupla[0][0]
                código[carrera_code] = {}
                código[carrera_code]["carrera"] = tupla[0][1]
                if i < len(fechas):
                    código[carrera_code]["fecha"] = fechas[i]

        patron_pdf = re.compile(r"(\d+)\.pdf$", re.MULTILINE)
        for pdf in horarios_pdf:
            código_carrera = patron_pdf.findall(pdf)
            if len(código_carrera) > 0 and código_carrera[0] in código:
                código[código_carrera[0]]["pdf"] = pdf

        for carrera_code, carrera_data in código.items():
            self.stdout.write(
                self.style.SUCCESS(
                    f'Carrera:"{carrera_data["carrera"]}"',
                ),
            )

            try:
                obj_carrera = Carrera.objects.get(pk=carrera_code)
                self.stdout.write(self.style.WARNING("Existente"))

                fecha = timezone.make_aware(
                    datetime.datetime.strptime(
                        carrera_data["fecha"],
                        self.patron_fecha,
                    ),
                )

                if obj_carrera.fecha() < fecha:
                    self.stdout.write(self.style.WARNING("Hay Cambios"))
                    obj_carrera.fecha = fecha
                    obj_carrera.nombre = carrera_data["carrera"]
                    if "pdf" in carrera_data:
                        obj_carrera.pdf = carrera_data["pdf"]
                    obj_carrera.save()
                else:
                    self.stdout.write(self.style.WARNING("Sin Cambios"))
            except Carrera.DoesNotExist:
                self.stdout.write(self.style.WARNING("Nueva"))
                obj_carrera = Carrera.objects.create(código=carrera_code)
                fecha = timezone.make_aware(
                    datetime.datetime.strptime(
                        carrera_data["fecha"],
                        self.patron_fecha,
                    ),
                )
                obj_carrera.fecha = fecha
                obj_carrera.nombre = carrera_data["carrera"]
                if "pdf" in carrera_data:
                    obj_carrera.pdf = carrera_data["pdf"]
                obj_carrera.save()
            self.descargar(carrera_code, obj_carrera.código)
        self.stdout.write(self.style.SUCCESS("Terminado"))

    def descargar(self, código, carrera):
        obj_carrera = Carrera.objects.get(pk=carrera)
        u = urllib.request.urlopen(obj_carrera.pdf)
        meta = u.info()
        fecha = timezone.make_aware(
            datetime.datetime.strptime(
                str(meta["Last-Modified"]),
                self.patron_fecha_apache,
            ),
            timezone=timezone.get_current_timezone(),
        )
        if obj_carrera.fecha_pdf < fecha:
            obj_carrera.fecha_pdf = fecha
            self.stdout.write(
                self.style.WARNING(
                    "PDFNuevo "
                    + obj_carrera.fecha_pdf.strftime("%Y-%m-%d_%H:%M:%S %z %Z"),
                ),
            )
            Path(
                f"{settings.STATIC_ROOT}/{obj_carrera.nombre}_{código}",
            ).mkdir(
                parents=True,
                exist_ok=True,
            )
            with Path(
                f"{settings.STATIC_ROOT}/{obj_carrera.nombre}_{código}/{obj_carrera.fecha_pdf.strftime('%Y-%m-%d_%H:%M:%S')}.pdf",
            ).open("wb") as f:
                c = pycurl.Curl()
                c.setopt(c.URL, obj_carrera.pdf)
                c.setopt(c.NOPROGRESS, False)
                c.setopt(c.XFERINFOFUNCTION, self.progress)
                c.setopt(c.WRITEDATA, f)
                c.perform()
                c.close()
            obj_carrera.save()

    # Callback function invoked when download/upload has progress
    def progress(self, download_t, download_d, upload_t, upload_d):
        if download_t != 0:
            self.stdout.write(
                self.style.SUCCESS(int(download_d * 100 / download_t), ending="\r")
            )

    def generar_textos(self):
        carreras = Carrera.objects.all()
        for carrera in carreras:
            ruta_base = (
                settings.STATIC_ROOT
                + "/"
                + carrera.nombre
                + "_"
                + str(carrera.código)
                + "/"
            )
            fecha = carrera.fecha_pdf.astimezone(timezone.get_current_timezone())

            archivo = fecha.strftime("%Y-%m-%d_%H:%M:%S")
            subprocess.run(
                ["pdftotext", "-layout", "-nopgbrk", ruta_base + archivo + ".pdf"],
                check=False,
                stdout=subprocess.PIPE,
            )
            subprocess.run(
                ["sed", "-i", "s/¥/Ñ/g", ruta_base + archivo + ".txt"],
                check=False,
                stdout=subprocess.PIPE,
            )

    def procesar_horarios(self):
        carreras = Carrera.objects.all()
        for carrera in carreras:
            ruta_base = (
                settings.STATIC_ROOT
                + "/"
                + carrera.nombre
                + "_"
                + str(carrera.código)
                + "/"
            )
            fecha = carrera.fecha_pdf.astimezone(timezone.get_current_timezone())

            archivo = fecha.strftime("%Y-%m-%d_%H:%M:%S")
            self.cosechar(ruta_base + archivo, carrera)

    def cosechar(self, base, objCarrera):
        exp_base = r"(\d{5,}) ([A-ZÑ. ]+) (\d{1,2})\s+([VISALUMIJ]{2}) (\d{3,4})-"
        r"(\d{3,4})\((\d{3}[A-Z]?)\)\s+([A-ZÑ. ]+)"
        exp_a = re.compile(r"\(\*\) " + exp_base)
        exp_d = re.compile(r"\s+" + exp_base)
        nivel = "A"

        for linea in fileinput.input(base + ".txt"):
            dato_a = exp_a.findall(linea)
            dato_d = exp_d.findall(linea)
            nivel_tmp = self.patron_nivel.findall(linea)
            if len(nivel_tmp) > 0:
                nivel = nivel_tmp[0]

            if len(dato_a) > 0:
                # print('ayudante '+str(datoA[0]))
                código = dato_a[0][0]
                materia = dato_a[0][1].strip()
                grupo = dato_a[0][2]
                día = dato_a[0][3]
                inicia = dato_a[0][4]
                termina = dato_a[0][5]
                aula = dato_a[0][6]
                ayudante = dato_a[0][7]
                self.crea_materia(
                    materia,
                    False,
                    self.crea(Ayudante, ayudante),
                    código,
                    grupo,
                    aula,
                    inicia,
                    termina,
                    día,
                    nivel,
                    objCarrera,
                )
            if len(dato_d) > 0:
                # print('docente '+str(datoD[0]))
                código = dato_d[0][0]
                materia = dato_d[0][1].strip()
                grupo = dato_d[0][2]
                día = dato_d[0][3]
                inicia = dato_d[0][4]
                termina = dato_d[0][5]
                aula = dato_d[0][6]
                docente = dato_d[0][7]

                self.crea_materia(
                    materia,
                    True,
                    self.crea(Docente, docente),
                    código,
                    grupo,
                    aula,
                    inicia,
                    termina,
                    día,
                    nivel,
                    objCarrera,
                )

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
                código=código_nivel_materia,
                materia=mat,
                carrera=carrera,
                nivel=nivel,
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
        ini_t = self.patron_hora.findall(inicia)[0]
        ini = ini_t[0] + ":" + ini_t[1]
        fin_t = self.patron_hora.findall(termina)[0]
        fin = fin_t[0] + ":" + fin_t[1]
        # ini = time.strptime(inicia, "%H%M")
        # fin = time.strptime(termina, "%H%M")
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
