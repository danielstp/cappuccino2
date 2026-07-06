# Guía para Agentes de IA - Cappuccino2

Bienvenido al repositorio de **Cappuccino2**. Este archivo sirve como una guía técnica detallada para que cualquier agente de IA pueda entender el contexto, las herramientas, la estructura de carpetas y las reglas críticas para el correcto desarrollo y mantenimiento del proyecto.

---

## 1. Descripción general del proyecto
**Cappuccino2** es una aplicación web basada en el framework web Django, diseñada específicamente para automatizar la recopilación, el procesamiento y la distribución de los horarios de clases de la Facultad de Ciencias y Tecnología (FCYT) de la Universidad Mayor de San Simón (UMSS) en Cochabamba, Bolivia.

El flujo general de la aplicación consiste en:
1. Conectarse y parsear el sitio web de la FCYT para detectar nuevos horarios publicados.
2. Descargar los archivos PDF de horarios correspondientes a las diferentes carreras académicas.
3. Procesar y extraer la información en texto plano de dichos PDFs empleando la utilidad `pdftotext` (envoltura sobre Poppler C++) y expresiones regulares (`re` de Python).
4. Guardar y estructurar la información extraída en una base de datos relacional PostgreSQL.
5. Servir estos datos estructurados a través de una API REST rápida y tipada usando `django-ninja`, y una interfaz web que utiliza `django-grappelli` para la administración y Bootstrap 5 para el frontend.

---

## 2. Stack tecnológico
- **Lenguaje principal**: Python 3.13.* (manejado mediante `uv`)
- **Framework Web**: Django 6.0.3 from https://github.com/cookiecutter/cookiecutter-django
- **Administrador de paquetes y entornos**: `uv` (Astral)
- **Base de datos**: PostgreSQL (utiliza el driver `psycopg` versión 3)
- **API REST**: Django Ninja 1.6.2 (servida en `/api/` y documentada en `/api/docs/` protegida para personal de administración)
- **Motor de Plantillas y Estilo**: Django Templates con Crispy Forms (`crispy-bootstrap5` y `django-crispy-forms`)
- **Panel de Administración**: Django Admin personalizado con `django-grappelli`
- **Gestión de Estáticos**: `django-compressor` y `whitenoise`
- **Autenticación y Cuentas**: `django-allauth` con soporte de MFA
- **Procesamiento de PDF**: `pdftotext` (dependencia nativa que requiere `poppler` instalado en el sistema operativo)
- **Lector/Parser de HTML**: `parsel` (Scrapy Selector) y descargas con `urllib.request` + `pycurl`
- **Linters y Formateadores**:
  - Ruff (v0.15.7) para linting y formateo de Python.
  - djLint (v1.36.4) para formatear plantillas HTML.
- **Tipado estático**: `mypy` (v1.19.1) con `django-stubs`
- **Pruebas unitarias**: `pytest` con `pytest-django`, `pytest-sugar` y `coverage`

---

## 3. Estructura de carpetas principal
- `/cappuccino2/`: Carpeta raíz del código fuente Django.
  - `horario/`: Aplicación principal que contiene la lógica de scraping y procesamiento de horarios.
    - `management/commands/`: Comandos personalizados de Django.
      - `horario.py`: Comando core que descarga los PDFs, extrae la información con regex complejos y popoula los modelos.
      - `horario_plano.py`: Comando auxiliar para procesar o depurar texto plano.
    - `models.py`: Modelos principales (`Carrera`, `Gestión`, `Actualización`, `Docente`, `Ayudante`, `Materia`, `NivelMateria`, `Aula`, `Grupo`, `Horario`).
    - `admin.py`: Registros y personalizaciones del panel de administración.
  - `users/`: Aplicación Django para la gestión de usuarios, perfiles y APIs específicas de usuario.
    - `api/`: Controladores/Vistas de Django Ninja para los usuarios.
    - `tests/`: Pruebas unitarias específicas para la aplicación de usuarios (modelos, formularios, managers, vistas, endpoints API).
  - `templates/`: Plantillas HTML organizadas por páginas, cuentas y layout.
  - `static/`: Recursos estáticos locales como CSS, JS e imágenes.
- `/config/`: Configuración global del proyecto Django.
  - `settings/`: Configuración de entornos.
    - `base.py`: Ajustes comunes y heredados.
    - `local.py`: Ajustes de desarrollo local.
    - `production.py`: Ajustes para entorno de producción.
    - `test.py`: Ajustes para la suite de pruebas unitarias.
  - `urls.py`: Enrutador global de URLs (grappelli, admin, allauth, users, horario y api).
  - `api.py`: Instanciación y enrutamiento principal de `NinjaAPI`.
- `/bin/`: Scripts ejecutables de automatización (ej. `post_compile` para compilación y recolección de estáticos en despliegues).
- `/utility/`: Scripts para configurar dependencias del sistema operativo (por ejemplo, dependencias APT en Debian/Ubuntu como `libpq-dev`, `build-essential`, `python3-dev`).
- `/tests/`: Pruebas unitarias a nivel de proyecto (ej. `test_merge_production_dotenvs_in_dotenv.py`).

---

## 4. Instalación y arranque (desarrollo local)
Para levantar el entorno local, sigue estos comandos en orden:

1. **Instalar dependencias del sistema operativo** (requeridas para compilar `psycopg`, `pillow` y `pdftotext`):
   En Debian/Ubuntu:
   ```bash
   sudo apt-get update
   sudo apt-get install -y build-essential python3-dev libpq-dev libtiff5-dev libjpeg-dev zlib1g-dev libfreetype6-dev liblcms2-dev libwebp-dev libgraphviz-dev gettext libpoppler-cpp-dev pkg-config
   ```
   *Nota: `libpoppler-cpp-dev` y `pkg-config` son esenciales para que la librería Python `pdftotext` compile correctamente.*

2. **Instalar `uv`** (si no está instalado):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. **Instalar dependencias del proyecto y crear el entorno virtual**:
   ```bash
   uv sync
   ```
   Este comando leerá `pyproject.toml` y generará la carpeta `.venv/` con la versión exacta de Python (3.13) y librerías requeridas.

4. **Configurar Variables de Entorno**:
   El proyecto lee variables desde un archivo `.env` en la raíz si `DJANGO_READ_DOT_ENV_FILE=True` está configurado.
   Crea un archivo `.env` basándote en las configuraciones locales:
   ```bash
   DJANGO_READ_DOT_ENV_FILE=True
   DATABASE_URL=postgres://tu_usuario:tu_password@localhost:5432/cappuccino2
   REDIS_URL=redis://localhost:6379/0
   ```

5. **Aplicar Migraciones**:
   ```bash
   uv run python manage.py migrate
   ```

6. **Crear Superusuario**:
   ```bash
   uv run python manage.py createsuperuser
   ```

7. **Iniciar el servidor de desarrollo**:
   ```bash
   uv run python manage.py runserver
   ```

---

## 5. Convenciones de código y estilo
- **Formateo y Calidad**: El código Python debe seguir estrictamente las reglas de **Ruff**. Las reglas están definidas en `pyproject.toml` e ignoran intencionalmente `RUF012`, `S101` y `SIM102`. Ruff se encarga tanto del linter como del formateador.
- **Formateo de Plantillas**: Las plantillas HTML se formatean con **djLint** usando un espaciado de 2 espacios (indent=2) y perfil de Django.
- **Tipado Estático**: Se prefiere el uso de anotaciones de tipos en firmas de funciones. `mypy` comprueba estáticamente el proyecto con soporte de `django-stubs`.
- **Pre-commit**: El repositorio está integrado con `pre-commit` (configurado en `.pre-commit-config.yaml`). Al hacer un commit, se ejecutan automáticamente hooks de limpieza, Ruff, pyproject-fmt y djLint. Asegúrate de instalar pre-commit en tu entorno de desarrollo local con `pre-commit install`.
- **Vistas y APIs**: Las APIs se construyen preferentemente con `django-ninja` (NinjaAPI) usando enrutadores y esquemas pydantic para validación y serialización de datos.

---

## 6. Reglas importantes para no romper nada
- **Lógica de Claves Primarias (PKs) Personalizadas**:
  Los modelos principales de `cappuccino2/horario/models.py` sobrescriben el método `save()` para generar IDs basados en su contenido. **Nunca** crees registros de forma manual asignando IDs arbitrarios o alterando estas funciones, ya que romperás la integridad referencial y las búsquedas:
  - `Gestión`: `id = f"{self.año}.{self.semestre}"` (ej. `"2025.1"`).
  - `Actualización`: ID dinámico basado en `genera_pk(gestion, fecha)`.
  - `NivelMateria`: ID compuesto de la forma `nivel-materia_código-carrera_código` (ej. `"A-12345-45"`).
  - `Grupo`: ID compuesto de la forma `grupo-materia_código-actualización_id`.
  - `Horario`: ID compuesto de la forma `día-inicio_HMM-grupo_código` (ej. `"LU-0815-grupo_pk"`).
- **Procesamiento de Horarios (`horario.py`)**:
  - El comando `python manage.py horario` procesa los PDFs usando hilos (`ThreadPoolExecutor`). Ten en cuenta las conexiones de base de datos simultáneas al modificar su concurrencia.
  - Las expresiones regulares (`PATRON_*`) en `horario.py` están fuertemente acopladas al formato oficial del PDF del CPD de la FCYT-UMSS. Modificar un patrón sin verificar puede provocar que la extracción falle silenciosamente o cause un error de procesamiento.
- **Enrutamiento de URLs**:
  - `cappuccino2/horario/urls.py` requiere tener una variable `urlpatterns` declarada (actualmente vacía), de lo contrario romperá la carga de URLs a nivel global en Django y lanzará un error `ImproperlyConfigured`.

---

## 7. Comandos más usados
Todos los comandos deben ejecutarse precedidos por `uv run` para asegurar que se use el entorno virtual correcto:

- **Iniciar Servidor**: `uv run python manage.py runserver`
- **Ejecutar Pruebas**: `uv run pytest` (o `.venv/bin/pytest`)
- **Ejecutar Scraper de Horarios**: `uv run python manage.py horario`
- **Crear Migraciones**: `uv run python manage.py makemigrations`
- **Aplicar Migraciones**: `uv run python manage.py migrate`
- **Ejecutar Linter de Python (Ruff)**: `uv run ruff check`
- **Formatear Código Python (Ruff)**: `uv run ruff format`
- **Ejecutar Linter de Tipos (Mypy)**: `uv run mypy cappuccino2`
- **Formatear Plantillas HTML**: `uv run djlint . --reformat`
- **Compilar Traducciones**: `uv run python manage.py compilemessages`
