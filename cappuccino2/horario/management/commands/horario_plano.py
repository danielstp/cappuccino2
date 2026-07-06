import re
from datetime import datetime as dt
from pathlib import Path
from typing import Any

import pdftotext
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from cappuccino2.horario.models import Actualización as Actualizacion
from cappuccino2.horario.models import Aula
from cappuccino2.horario.models import Ayudante
from cappuccino2.horario.models import Carrera
from cappuccino2.horario.models import Docente
from cappuccino2.horario.models import Gestión as Gestion
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
        r"^Plan: (?P<carrera>[\w\s\.\(\)]+)\((?P<codigoCarrera>\d+)\)\s+Nivel de "
        r"Estudios:\s(?P<nivel>[A-L])$",
        re.IGNORECASE + re.MULTILINE,
    )
    # (*) SisMat, Nombre Materia, Grupo, Horario, Nombre del Docente
    #  ww⮤ Ayudantía, Práctica o Laboratorio
    #
    patron_horario = re.compile(
        r"^\(?(?P<ayudantia>\*?)\)?\s*(?P<codigoMateria>\d+)\s(?P<materia>[\w\s]+)\s+(?P<grupo>\w+)\s+(?P<dia>LU|MA|MI|JU|VI|SA)\s+"
        r"(?P<horaInicioFin>\d{3,4}-\d{3,4})\((?P<aula>\d+[A-Z]?)\)\s+(?P<docente>[\s\w\.]+)$",
        re.IGNORECASE + re.MULTILINE,
    )

    patron_hora = re.compile(r"(\d{1,2})(\d{2})")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.cola_pdfs: list[tuple[Any, str]] = []

    def handle(self, *args: Any, **options: Any) -> None:
        self.obtener_archivos()
        self.procesar_horarios()

    def obtener_archivos(self) -> None:
        ruta_base = Path(f"{settings.STATIC_ROOT}/horarios/")
        if not ruta_base.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"La ruta {ruta_base} no existe. "
                    "Crea la carpeta y coloca los archivos PDF allí.",
                ),
            )
            return

        for archivo in (
            x for x in ruta_base.iterdir() if x.is_file() if x.match("*.pdf")
        ):
            with archivo.open("rb") as f:
                self.cola_pdfs.append(
                    (pdftotext.PDF(f, physical=True), archivo.name),
                )

    def procesar_horarios(self) -> None:
        for archivo_pdf in self.cola_pdfs:
            for pagina in archivo_pdf[0]:
                self.cosechar(pagina, archivo_pdf[1])

    def cosechar(self, pagina: str, nombre_archivo: str) -> None:
        self.stdout.write(f"procesando... {nombre_archivo} ...")

        semestre_match = Command.patron_semestre.search(pagina)
        fecha_match = Command.patron_fecha.search(pagina)
        nivel_match = Command.patron_nivel.search(pagina)

        if not (semestre_match and fecha_match and nivel_match):
            self.stdout.write(
                self.style.WARNING(
                    "No se pudieron encontrar cabeceras válidas "
                    f"en la página del archivo {nombre_archivo}.",
                ),
            )
            return

        semestre = semestre_match.groupdict()["semestre"]
        fecha = fecha_match.groupdict()["fecha"]
        nivel = nivel_match.groupdict()["nivel"]
        carrera_nombre = nivel_match.groupdict()["carrera"]
        codigo_carrera = nivel_match.groupdict()["codigoCarrera"]

        self.stdout.write(
            f"{semestre = }, {fecha = }, "
            f"carrera_nombre = {carrera_nombre.strip()}({codigo_carrera}), "
            f"{nivel = }",
        )

        # Get or create Carrera
        carrera_obj, _ = Carrera.objects.get_or_create(
            código=int(codigo_carrera),
            defaults={"nombre": carrera_nombre.strip()},
        )

        # Parse semestre (e.g. "1 del 2025")
        match_sem = re.search(r"(\d+)\s+del\s+(\d+)", semestre)
        if match_sem:
            semestre_num = match_sem.group(1)
            ano_num = int(match_sem.group(2))
        else:
            semestre_num = "1"
            ano_num = 2026

        # Get or create Gestión
        today_date = timezone.now().date()
        gestion, _ = Gestion.objects.get_or_create(
            semestre=semestre_num,
            año=ano_num,
            defaults={
                "inicio": today_date,
                "fin": today_date,
            },
        )

        # Parse fecha (e.g. "24/06/2026")
        try:
            fecha_dt = dt.strptime(fecha, "%d/%m/%Y").replace(
                tzinfo=timezone.get_current_timezone(),
            )
        except ValueError:
            fecha_dt = timezone.now()

        # Get or create Actualización
        actualizacion, _ = Actualizacion.objects.get_or_create(
            fecha=fecha_dt,
            gestión=gestion,
        )
        actualizacion.carreras.add(carrera_obj)
        actualizacion.save()

        for hora in Command.patron_horario.finditer(pagina):
            data = hora.groupdict()
            self.stdout.write(str(data))

            nombre_docente = data["docente"].strip()
            is_docente = not bool(data["ayudantia"])

            if is_docente:
                docente_obj = self.crea(Docente, nombre_docente)
            else:
                docente_obj = self.crea(Ayudante, nombre_docente)

            # Split horaInicioFin (e.g. "0815-0945")
            try:
                inicia, termina = data["horaInicioFin"].split("-")
            except ValueError:
                continue

            self.crea_materia(
                materia=data["materia"].strip(),
                docente=is_docente,
                obj=docente_obj,
                codigo=int(data["codigoMateria"]),
                grupo=data["grupo"],
                aula=data["aula"],
                inicia=inicia,
                termina=termina,
                dia=data["dia"],
                nivel=nivel,
                carrera=carrera_obj,
                actualizacion=actualizacion,
            )

    def crea(self, tipo: Any, nombre: str) -> Any:
        obj, _ = tipo.objects.get_or_create(nombre=nombre)
        return obj

    def crea_materia(  # noqa: PLR0913
        self,
        materia: str,
        docente: bool,  # noqa: FBT001
        obj: Any,
        codigo: int,
        grupo: str,
        aula: str,
        inicia: str,
        termina: str,
        dia: str,
        nivel: str,
        carrera: Carrera,
        actualizacion: Actualizacion,
    ) -> None:
        mat, _ = Materia.objects.get_or_create(
            código=codigo,
            defaults={"nombre": materia},
        )

        codigo_nivel_materia = NivelMateria.genera_pk(nivel, codigo, carrera.código)
        NivelMateria.objects.get_or_create(
            código=codigo_nivel_materia,
            defaults={
                "materia": mat,
                "carrera": carrera,
                "nivel": nivel,
            },
        )

        codigo_grupo = Grupo.genera_pk(grupo, mat, actualizacion)
        if docente:
            defaults = {"docente": obj, "materia": mat}
        else:
            defaults = {"ayudante": obj, "materia": mat}

        grup, creado = Grupo.objects.get_or_create(
            código=codigo_grupo,
            grupo=grupo,
            actualización=actualizacion,
            defaults=defaults,
        )
        if not creado:
            if docente:
                grup.docente = obj
            else:
                grup.ayudante = obj
            grup.save()

        aul, _ = Aula.objects.get_or_create(código=aula)

        try:
            ini_t = self.patron_hora.findall(inicia)[0]
            ini = f"{int(ini_t[0]):02d}:{int(ini_t[1]):02d}"
            fin_t = self.patron_hora.findall(termina)[0]
            fin = f"{int(fin_t[0]):02d}:{int(fin_t[1]):02d}"
        except IndexError:
            return

        try:
            time_inicio = (
                dt.strptime(ini, "%H:%M")
                .replace(
                    tzinfo=timezone.get_current_timezone(),
                )
                .time()
            )
            time_fin = (
                dt.strptime(fin, "%H:%M")
                .replace(
                    tzinfo=timezone.get_current_timezone(),
                )
                .time()
            )
        except ValueError:
            return

        codigo_horario = f"{dia}-{time_inicio.strftime('%H%M')}-{grup.código}"
        Horario.objects.get_or_create(
            código=codigo_horario,
            defaults={
                "grupo": grup,
                "aula": aul,
                "inicio": time_inicio,
                "fin": time_fin,
                "día": dia,
            },
        )
