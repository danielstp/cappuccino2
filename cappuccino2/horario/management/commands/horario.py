import logging
import re
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed
from datetime import datetime as dt
from pathlib import Path
from pprint import pprint
from typing import Any
from typing import Final
from typing import final

import pdftotext
import pycurl
import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError
from django.utils import timezone
from parsel import Selector
from tqdm import tqdm

from cappuccino2.horario.models import Actualización
from cappuccino2.horario.models import Aula
from cappuccino2.horario.models import Ayudante
from cappuccino2.horario.models import Carrera
from cappuccino2.horario.models import Docente
from cappuccino2.horario.models import Gestión
from cappuccino2.horario.models import Grupo
from cappuccino2.horario.models import Horario
from cappuccino2.horario.models import Materia
from cappuccino2.horario.models import NivelMateria

# Configure structured logging
logger = logging.getLogger(__name__)


@final
class Command(BaseCommand):
    """Django management command to update schedules from FCYT - UMSS careers."""

    help = "Actualizar Horarios"

    # Constants
    URL_HORARIOS: Final[str] = (
        "https://sagaa.fcyt.umss.edu.bo/horarios/HorariosFCyT.php"
    )
    TIMEOUT: Final[int] = getattr(settings, "TIMEOUT", 30)

    # Compiled Regex Patterns
    PATRON_SEMESTRE_ANO: Final[re.Pattern] = re.compile(r"HORARIOS\s+(\d+)-(\d+)")
    PATRON_CARRERA_INFO: Final[re.Pattern] = re.compile(r"^(\d+)\s(\w[\w\- ()]+)$")

    # Complex patterns with flags
    PATRON_DÍA: Final[re.Pattern] = re.compile(
        r"^(?P<grupo>\d?[A-Z]?[\d]{0,2})(?:\s*(?P<ayudante>\[[PT]{1,2}\]))?\s*"
        r"(?P<docente>[A-ZÑ][A-ZÑ\s\.]{6,49}[\w\.])\s+(?P<día>LU|MA|MI|JU|VI|SA|DO)\s+"
        r"(?P<hora_inicio>(6|7|8|9|10|11|12|13|14|15|16|17|18|19|20)(00|15|30|45))\s?-"
        r"(?P<hora_fin>(08|09|10|11|12|13|14|15|16|17|18|19|20|21)(00|15|30|45))\s+"
        r"(?P<aula>\w?\d[\d\w]+|AULVIR|ALIM)",
        flags=re.MULTILINE + re.IGNORECASE + re.UNICODE,
    )
    PATRON_MATERIA_LINE: Final[re.Pattern] = re.compile(
        r"^(?P<nivel>[A-K])\s+(?P<código>\d{5,9})\s+(?P<materia>\w[\w\- ()]{5,60}\w)$",
        flags=re.MULTILINE + re.IGNORECASE + re.UNICODE,
    )
    PATRON_CABECERA: Final[re.Pattern] = re.compile(
        r"UNIVERSIDAD MAYOR DE SAN SIMON\s*FACULTAD DE CIENCIAS Y TECNOLOGÍA\s+HORARIO "
        r"DE CLASES\s+(?P<carrera>LICENCIATURA\s+EN\s+\w[\w ]+\w)\s+Gestión\s+Académica"
        r"\s+(?P<semestre>\d)/(?P<año>\d{4})",
        flags=re.MULTILINE + re.IGNORECASE + re.UNICODE,
    )
    PATRON_PIE: Final[re.Pattern] = re.compile(
        r"Procesado\s*CPD\s*-\s*Facultad\s*de\s*Ciencias\s*y\s*Tecnología\s*Página\s*\d{1,2}\s*de\s*\d{1,3}",
        flags=re.MULTILINE + re.IGNORECASE + re.UNICODE,
    )
    PATRON_FECHA: Final[re.Pattern] = re.compile(
        r"(?P<fecha>\d{1,2}/\d{1,2}/\d{1,4}\s+\d{1,2}:\d{1,2}:\d{1,2}\s[AP]M)\s*",
        flags=re.MULTILINE + re.IGNORECASE + re.UNICODE,
    )
    PATRON_TÍTULO: Final[re.Pattern] = re.compile(
        r"\s*NIVEL\s*MATERIA\s*GRUPO\s*TIPO\s*DOCENTE\s*DIA\s*HORA\s*AULA\s*",
        flags=re.MULTILINE + re.IGNORECASE + re.UNICODE,
    )
    PATRON_AYUDANTE: Final[re.Pattern] = re.compile(r"^\[\w{1,2}]\s+\w+")

    # Date Formats
    FMT_FECHA: Final[str] = "%H:%M %d-%m-%Y"
    FMT_FECHA_APACHE: Final[str] = "%a, %d %b %Y %H:%M:%S %Z"

    def handle(self, *args: Any, **options: Any) -> None:
        """Main entry point for the command."""
        logger.info(
            self.style.SUCCESS("Iniciando el proceso de actualización de horarios"),
        )

        try:
            self._cargar_datos_de_origen()
            self.stdout.write(self.style.HTTP_REDIRECT("¡¡¡Horarios descargados!!!"))
            self._convirtiendo_recursos()
            self.stdout.write(self.style.HTTP_REDIRECT("¡¡¡PDF convertidos!!!"))
            self._procesando_horarios()
            self.stdout.write(self.style.HTTP_REDIRECT("¡¡¡Horarios procesados!!!"))
            logger.info(
                self.style.SUCCESS(
                    "Proceso de actualización de horarios completado exitosamente",
                ),
            )
        except Exception as e:
            msg = "Error durante la ejecución"
            logger.exception(self.style.ERROR(msg))
            raise CommandError(msg) from e

    def _setup_logging(self) -> None:
        """Configures logging for the command."""
        # Ensure we can see info logs in the console
        if not logger.handlers:
            handler = logging.StreamHandler(self.stdout)
            handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                self.style.SUCCESS("[%(levelname)s] %(message)s"),
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False

    # -------------------------------------------------------------------------
    # Phase 1: Download Resources
    # -------------------------------------------------------------------------

    def _cargar_datos_de_origen(self) -> None:
        """Downloads PDF schedules from the FCYT UMSS website."""
        logger.info(
            self.style.SQL_KEYWORD("Descargando horarios de: %s ..."), self.URL_HORARIOS
        )

        try:
            response_text = requests.get(self.URL_HORARIOS, timeout=self.TIMEOUT).text
        except requests.RequestException as e:
            msg = "No fue posible acceder a la pagina de los horarios"
            logger.exception(self.style.ERROR(msg))
            raise CommandError(msg) from e

        carreras_html = Selector(text=response_text)

        try:
            semestre_raw = carreras_html.xpath(
                "//table//tr/td[contains(@class, 'titulo5')]/b/text()",
            ).extract_first()

            if not semestre_raw:
                msg = "No se pudo encontrar la informacion del semestre en la pagina"
                logger.exception(self.style.ERROR(msg))
                raise ValueError(msg)

            semestre, año = self.PATRON_SEMESTRE_ANO.findall(semestre_raw)[0]
            semestre, año = int(semestre), int(año)

            logger.info(
                self.style.SQL_KEYWORD("Procesando Semestre: %s, Año: %s"),
                semestre,
                año,
            )

            carreras_xp = carreras_html.xpath(
                "//table//tr/td[contains(@class, 'normal')]/table//tr",
            ).pop()

            xpath_common = "//tr[contains(@class, 'celdaColorResultado3') or contains("
            xpath_common += "@class, 'celdaColorResultado2')]"
            carrera_names = carreras_xp.xpath(
                f"{xpath_common}/td[2]/div/font/text()",
            ).extract()
            fechas = carreras_xp.xpath(
                f"{xpath_common}/td[4]/div/font/text()",
            ).extract()
            pdf_urls = carreras_xp.xpath(
                f"{xpath_common}/td[3]/div/font/a/@href",
            ).extract()

            tasks = []
            for i, carrera_raw in enumerate(carrera_names):
                tasks.append(
                    (
                        carrera_raw.strip(),
                        fechas[i].strip(),
                        pdf_urls[i].strip(),
                        semestre,
                        año,
                    ),
                )

            max_workers = min(len(tasks), 16)
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = [
                    executor.submit(self._process_carrera_entry, *task)
                    for task in tasks
                ]
                for _ in tqdm(
                    as_completed(futures),
                    total=len(futures),
                    desc="Descargando PDFs",
                    unit="carrera",
                ):
                    pass

        except (IndexError, ValueError) as e:
            logger.exception(self.style.ERROR("Error parsing HTML content"))
            msg = "Error parsing HTML content"
            logger.exception(msg)
            raise CommandError(msg) from e

    def _process_carrera_entry(
        self,
        carrera_raw: str,
        fecha_str: str,
        pdf_url: str,
        semestre: int,
        año: int,
    ) -> None:
        """Processes a single career entry from the main page."""
        fecha = timezone.make_aware(
            dt.strptime(fecha_str, self.FMT_FECHA),
            timezone.get_current_timezone(),
        )

        match = self.PATRON_CARRERA_INFO.findall(carrera_raw)
        if not match:
            logger.warning(
                self.style.WARNING("Could not parse career info: %s"),
                carrera_raw,
            )
            return

        código, nombre = match[0]
        logger.info(
            self.style.SUCCESS("Found Carrera: %s (%s) - PDF: %s"),
            nombre,
            código,
            pdf_url,
        )

        carrera, actualización = self._create_or_update_carrera(
            código=int(código),
            nombre=nombre,
            fecha=fecha,
            url_pdf=pdf_url,
            año=año,
            semestre=semestre,
        )

        self._download_pdf(carrera, actualización)

    def _create_or_update_carrera(
        self,
        código: int,
        nombre: str,
        fecha: dt,
        url_pdf: str,
        semestre: int,
        año: int,
    ) -> tuple[Carrera, Actualización]:
        """Creates or updates database entries for the career."""
        gestión, created_g = Gestión.objects.get_or_create(
            semestre=semestre,
            año=año,
            defaults={"inicio": timezone.now(), "fin": timezone.now()},
        )
        if created_g:
            logger.info(self.style.SUCCESS("Nueva Gestión creada: %s"), gestión)

        actualización, created_a = Actualización.objects.get_or_create(
            fecha=fecha,
            gestión=gestión,
            defaults={"url_pdf": url_pdf},
        )
        if created_a:
            logger.info(
                self.style.SUCCESS("Nueva Actualización creada: %s"),
                actualización,
            )

        carrera, created_c = Carrera.objects.get_or_create(
            código=código,
            defaults={"nombre": nombre},
        )
        if created_c:
            logger.info(self.style.SUCCESS("Nueva Carrera creada: %s"), carrera)

        actualización.carreras.add(carrera)
        actualización.save()

        return carrera, actualización

    def _download_pdf(self, carrera: Carrera, actualización: Actualización) -> None:
        """Downloads the PDF file for a career."""
        url = self._ensure_https(actualización.url_pdf)

        try:
            with urllib.request.urlopen(url) as u:
                meta = u.info()
                last_modified = meta.get("Last-Modified")
                if last_modified:
                    fecha_pdf = timezone.make_aware(
                        dt.strptime(str(last_modified), self.FMT_FECHA_APACHE),
                        timezone=timezone.get_current_timezone(),
                    )
                    actualización.fecha_pdf = fecha_pdf
                    logger.info(
                        self.style.SUCCESS("Fecha actualizada del PDF: %s"),
                        fecha_pdf,
                    )

            output_dir = (
                Path(settings.STATIC_ROOT) / f"{carrera.nombre}_{carrera.código}"
            )
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"{actualización.id}.pdf"

            if output_path.exists():
                logger.info(
                    self.style.SUCCESS("El archivo PDF ya existe: %s"), output_path
                )
                return

            with output_path.open("wb") as f:
                c = pycurl.Curl()
                c.setopt(c.URL, url)
                c.setopt(c.NOPROGRESS, True)

                c.setopt(c.WRITEDATA, f)
                c.setopt(c.FOLLOWLOCATION, True)
                c.setopt(c.MAXREDIRS, 10)
                c.setopt(c.TIMEOUT, self.TIMEOUT)
                c.setopt(c.CONNECTTIMEOUT, self.TIMEOUT)
                c.setopt(c.NOSIGNAL, True)
                try:
                    c.perform()
                finally:
                    c.close()

            actualización.save()

        except Exception:
            logger.exception("Failed to download PDF for %s", carrera.nombre)
            # We don't raise here to allow other downloads to proceed

    def _ensure_https(self, url: str) -> str:
        """Ensures the URL uses HTTPS."""
        clean_url = url.strip()
        if clean_url.lower().startswith("https://"):
            return clean_url
        if clean_url.lower().startswith("http://"):
            return "https://" + clean_url[7:]
        return "https://" + clean_url

    # -------------------------------------------------------------------------
    # Phase 2: Convert Resources (PDF -> Text)
    # -------------------------------------------------------------------------

    def _convirtiendo_recursos(self) -> None:
        """Converts downloaded PDFs to text files."""
        logger.info("Convirtiendo PDFs a texto plano...")
        carreras = Carrera.objects.all()

        # This could also be parallelized if needed, but subprocess calls are already
        # somewhat independent
        for carrera in carreras:
            try:
                actualización = Actualización.objects.filter(carreras=carrera).latest(
                    "fecha",
                )
                base_path = (
                    Path(settings.STATIC_ROOT) / f"{carrera.nombre}_{carrera.código}"
                )
                pdf_path = base_path / f"{actualización.id}.pdf"

                if not pdf_path.exists():
                    logger.warning("PDF not found for %s: %s", carrera.nombre, pdf_path)
                    continue

            except Actualización.DoesNotExist:
                logger.warning(
                    "No se encontró una Actualización para %s",
                    carrera.nombre,
                )
            except Exception:
                logger.exception("Error al convertir recursos para %s", carrera.nombre)

    # -------------------------------------------------------------------------
    # Phase 3: Process Schedules (Text -> DB)
    # -------------------------------------------------------------------------

    def _procesando_horarios(self) -> None:
        """Parses text files and updates the database, using parallel processing."""
        logger.info(self.style.SQL_KEYWORD("Procesando horarios..."))
        carreras = list(Carrera.objects.all())

        # Use ThreadPoolExecutor for parallel processing
        # Adjust max_workers based on DB connection limits and CPU
        max_workers = min(len(carreras), 8)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_carrera = {
                executor.submit(self._process_single_carrera, carrera): carrera
                for carrera in carreras
            }

            for future in as_completed(future_to_carrera):
                carrera = future_to_carrera[future]
                try:
                    future.result()
                    logger.info("Procesado correctamente %s", carrera.nombre)
                except Exception:
                    logger.exception("Error procesando %s", carrera.nombre)

    def _process_single_carrera(self, carrera: Carrera) -> None:
        """Worker function to process a single career."""
        try:
            actualización = Actualización.objects.filter(carreras=carrera).latest(
                "fecha",
            )
            base_path = (
                Path(settings.STATIC_ROOT) / f"{carrera.nombre}_{carrera.código}"
            )
            pdf_path = base_path / f"{actualización.id}.pdf"

            if not pdf_path.exists():
                logger.warning(
                    self.style.WARNING("PDF file not found for %s: %s"),
                    carrera.nombre,
                    pdf_path,
                )
                return
            # Convert PDF to Text
            with Path.open(pdf_path, "rb") as f:
                txt = "\n".join(pdftotext.PDF(f, raw=True))
                # Fix encoding issues (sed replacement)
                txt = txt.replace("¥", "Ñ")
                # with Path.open(base_path / f"{actualización.id}.txt", "w") as f:
                #    f.write(txt)
                self._harvest_data(txt, carrera, actualización)
        except Actualización.DoesNotExist:
            logger.warning("No Actualización found for %s", carrera.nombre)

    def _harvest_data(
        self,
        content: str,
        carrera: Carrera,
        actualización: Actualización,
    ) -> None:
        """Reads and parses the text file."""
        logger.info(self.style.HTTP_REDIRECT("Extrayendo datos de %s"), carrera.nombre)
        base_path = Path(settings.STATIC_ROOT) / f"{carrera.nombre}_{carrera.código}"
        # Remover cabecera, título y pie
        full_text = self.PATRON_CABECERA.sub("", content)
        full_text = self.PATRON_TÍTULO.sub("", full_text)
        full_text = self.PATRON_PIE.sub("", full_text)
        full_text = self.PATRON_FECHA.sub("", full_text)
        with Path.open(base_path / f"{actualización.id}.txt", "w") as f:
            f.write(full_text)

        self._process_materia_block(full_text, carrera, actualización)

    def _process_materia_block(
        self,
        text: str,
        carrera: Carrera,
        actualización: Actualización,
    ) -> None:
        """Processes a block of text containing subjects (Materias)."""
        matches = list(self.PATRON_MATERIA_LINE.finditer(text))

        self.stdout.write(
            self.style.SQL_KEYWORD(
                "Encontrado %d materias para %s" % (len(matches), carrera.nombre)
            )
        )
        self.stdout.write(self.style.WARNING("Matches:"))
        pprint(matches)
        for i in range(len(matches)):
            match = matches[i]
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)

            materia_text = text[start:end]

            # Create Materia
            materia = self._create_materia(
                match.group("nivel"),
                match.group("código"),
                match.group("materia"),
                carrera,
            )

            # Process Groups for this Materia
            self._process_groups(materia_text, materia, actualización)

    def _create_materia(
        self,
        nivel: str,
        código: str,
        nombre: str,
        carrera: Carrera,
    ) -> Materia:
        """Creates or retrieves a Materia and its Nivel."""
        materia, _ = Materia.objects.get_or_create(
            código=código,
            defaults={"nombre": nombre},
        )
        NivelMateria.objects.get_or_create(
            nivel=nivel,
            materia=materia,
            carrera=carrera,
        )
        return materia

    def _process_groups(
        self,
        text: str,
        materia: Materia,
        actualización: Actualización,
    ) -> None:
        """Parses and creates groups/schedules for a subject."""
        for match in self.PATRON_DÍA.finditer(text):
            data = match.groupdict()
            data["actualización"] = actualización
            data["materia"] = materia
            self._crear_horario(data)

    def _crear_horario(self, data: dict[str, Any]) -> None:
        """Creates the schedule entry in the database."""
        # Handle Docente/Ayudante
        docente_name = data["docente"].replace("\n", " ").strip()
        is_docente = True
        docente = None
        self.stdout.write(self.style.HTTP_REDIRECT(f"Data: {data}"))
        self.stdout.write(self.style.HTTP_REDIRECT(f"Ayudante: {data['ayudante']}"))
        if data["ayudante"] is not None and data["ayudante"] != "":
            ayudante, ayudante_creado = Ayudante.objects.get_or_create(
                nombre=docente_name,
            )
            docente = ayudante
            is_docente = False
            if ayudante_creado:
                logger.info(self.style.SUCCESS("Ayudante creado: %s"), ayudante)
        else:
            docente, docente_creado = Docente.objects.get_or_create(
                nombre=docente_name,
            )
            is_docente = True
            if docente_creado:
                logger.info(self.style.SUCCESS("Docente creado: %s"), docente)

        # Handle Aula
        aula, aula_creado = Aula.objects.get_or_create(código=data["aula"])
        if aula_creado:
            logger.info(self.style.SUCCESS("Aula creada: %s"), aula)
        if is_docente:
            defaults = {"docente": docente, "materia": data["materia"]}
        else:
            defaults = {"ayudante": docente, "materia": data["materia"]}

        grupo, grupo_creado = Grupo.objects.get_or_create(
            grupo=data["grupo"],
            actualización=data["actualización"],
            defaults=defaults,
        )
        if grupo_creado:
            logger.info(self.style.SUCCESS("Grupo creado: %s"), grupo)

        # Parse times
        try:
            hora_inicio = dt.strptime(data["hora_inicio"].strip(), "%H%M")
            hora_fin = dt.strptime(data["hora_fin"].strip(), "%H%M")
        except ValueError:
            logger.warning(
                self.style.WARNING("Invalid time format: %s - %s"),
                data["hora_inicio"],
                data["hora_fin"],
            )
            return

        defaults = {
            "fin": hora_fin,
            "aula": aula,
        }
        # Create Horario
        horario, horario_creado = Horario.objects.get_or_create(
            grupo=grupo,
            día=data["día"],
            inicio=hora_inicio,
            defaults=defaults,
        )
        if horario_creado:
            logger.info(self.style.SUCCESS("Horario creado: %s"), horario)
