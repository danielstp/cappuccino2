import subprocess
import fileinput
import re
import requests
import datetime
import pycurl
import urllib.request
import os
import datetime
import time
import calendar
import time

from django.utils import timezone
from cappuccino2.horario.models import Carrera, Docente, Ayudante, Aula, Grupo, Horario, Materia, NivelMateria
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from parsel import Selector


class Command(BaseCommand):
    help = 'Actualizar Horarios'

    patroncódigo = re.compile(r'^(\d+)\s+(.*)$')
    patronNivel = re.compile(r'^Plan:[\s\d\w\(\)]+Nivel de Estudios:\s*([A-J])$')
    patronHora = re.compile(r'(\d{1,2})(\d{2})$')
    patronFecha = '%H:%M %d-%m-%Y'
    patronFechaApache = "%a, %d %b %Y %H:%M:%S %Z"

    def handle(self, *args, **options):
        self.descargarHorarios()
        self.generarTextos()
        self.procesarHorarios()

    def descargarHorarios(self, *args, **options):
        url = 'http://fcyt.umss.edu.bo/horarios/'
        text = requests.get(url).text
        selector = Selector(text=text)
        carreras = selector.xpath('/html/body/table[4]//tr/td[3]/table//tr[2]/td' +
                                  '/table//tr/td/table//tr/td[2]/div/font/text()').extract()
        fechas = selector.xpath('/html/body/table[4]//tr/td[3]/table//tr[2]/td' +
                                '/table//tr/td/table//tr/td[4]/div/font/text()').extract()
        horariosPDF = selector.xpath('/html/body/table[4]//tr/td[3]/table//tr[2]/td' +
                                     '/table//tr/td/table//tr/td[3]/div/font/a/@href').extract()
        código = {}
        c = 0
        for carrera in carreras:
            tupla = self.patroncódigo.findall(carrera)
            código[tupla[0][0]] = {}
            código[tupla[0][0]]['carrera'] = tupla[0][1]
            código[tupla[0][0]]['fecha'] = fechas[c]
            c = c + 1

        patronPDF = re.compile(r'(\d+)\.pdf$')
        for pdf in horariosPDF:
            pdf1 = patronPDF.findall(pdf)
            código[pdf1[0]]['pdf'] = pdf

        for carrera in código:
            self.stdout.write(self.style.SUCCESS('Carrera:"' + código[carrera]['carrera'] + '"'))

            try:
                objCar = Carrera.objects.get(pk=carrera)
                self.stdout.write(self.style.WARNING('Existente'))

                fecha = timezone.make_aware(datetime.datetime.strptime(
                    código[carrera]['fecha'], self.patronFecha), timezone=timezone.get_current_timezone())

                if(objCar.fecha < fecha):
                    self.stdout.write(self.style.WARNING('Hay Cambios'))
                    objCar.fecha = fecha
                    objCar.nombre = código[carrera]['carrera']
                    objCar.pdf = código[carrera]['pdf']
                    objCar.save()
                else:
                    self.stdout.write(self.style.WARNING('Sin Cambios'))
            except Carrera.DoesNotExist:
                self.stdout.write(self.style.WARNING('Nueva'))
                objCar = Carrera.objects.create(código=carrera)
                fecha = timezone.make_aware(datetime.datetime.strptime(
                    código[carrera]['fecha'], self.patronFecha), timezone=timezone.get_current_timezone())
                objCar.fecha = fecha
                objCar.nombre = código[carrera]['carrera']
                objCar.pdf = código[carrera]['pdf']
                objCar.save()
            self.descargar(carrera, objCar.código)
        self.stdout.write(self.style.SUCCESS('Terminado'))

    def descargar(self, código, carrera):
        objCarrera = Carrera.objects.get(pk=carrera)
        u = urllib.request.urlopen(objCarrera.pdf)
        meta = u.info()
        fecha = timezone.make_aware(datetime.datetime.strptime(
            str(meta["Last-Modified"]), self.patronFechaApache), timezone=timezone.get_current_timezone())
        if(objCarrera.fechaPDF < fecha):
            objCarrera.fechaPDF = fecha
            self.stdout.write(self.style.WARNING('PDFNuevo ' + objCarrera.fechaPDF.strftime('%Y-%m-%d_%H:%M:%S %z %Z')))
            if(not os.path.exists(settings.STATIC_ROOT + '/' + objCarrera.nombre + '_' + código)):
                os.makedirs(settings.STATIC_ROOT + '/' + objCarrera.nombre + '_' + código, exist_ok=True)
            with open(settings.STATIC_ROOT + '/' + objCarrera.nombre + '_' + código + '/' + objCarrera.fechaPDF.strftime('%Y-%m-%d_%H:%M:%S') + '.pdf', 'wb') as f:
                c = pycurl.Curl()
                c.setopt(c.URL, objCarrera.pdf)
                c.setopt(c.NOPROGRESS, False)
                c.setopt(c.XFERINFOFUNCTION, self.progress)
                c.setopt(c.WRITEDATA, f)
                c.perform()
                c.close()
            objCarrera.save()
            # self.cosechar(settings.STATIC_ROOT + '/' + código, objCarrera)

    # Callback function invoked when download/upload has progress
    def progress(self, download_t, download_d, upload_t, upload_d):
        if(download_t != 0):
            print(int(download_d * 100 / download_t), end='\r')

    def generarTextos(self):
        carreras = Carrera.objects.all()
        for carrera in carreras:
            rutaBase = settings.STATIC_ROOT + '/' + carrera.nombre + '_' + str(carrera.código) + '/'
            fecha = carrera.fechaPDF.astimezone(timezone.get_current_timezone())

            archivo = fecha.strftime('%Y-%m-%d_%H:%M:%S')
            p = subprocess.run(['pdftotext', '-layout', '-nopgbrk', rutaBase +
                                archivo + '.pdf'], stdout=subprocess.PIPE)
            p = subprocess.run(['sed', '-i', "s/¥/Ñ/g", rutaBase + archivo + '.txt'], stdout=subprocess.PIPE)

    def procesarHorarios(self):
        carreras = Carrera.objects.all()
        for carrera in carreras:
            rutaBase = settings.STATIC_ROOT + '/' + carrera.nombre + '_' + str(carrera.código) + '/'
            fecha = carrera.fechaPDF.astimezone(timezone.get_current_timezone())

            archivo = fecha.strftime('%Y-%m-%d_%H:%M:%S')
            self.cosechar(rutaBase + archivo, carrera)

    def cosechar(self, base, objCarrera):
        expBase = '(\d{5,}) ([A-ZÑ. ]+) (\d{1,2})\s+([VISALUMIJ]{2}) (\d{3,4})-(\d{3,4})\((\d{3}[A-Z]?)\)\s+([A-ZÑ. ]+)'
        expA = re.compile(r'\(\*\) ' + expBase)
        expD = re.compile(r'\s+' + expBase)
        nivel = 'A'

        for linea in fileinput.input(base + '.txt'):
            datoA = expA.findall(linea)
            datoD = expD.findall(linea)
            nivelTmp = self.patronNivel.findall(linea)
            if(len(nivelTmp) > 0):
                nivel = nivelTmp[0]

            if(len(datoA) > 0):
                # print('ayudante '+str(datoA[0]))
                código = datoA[0][0]
                materia = datoA[0][1].strip()
                grupo = datoA[0][2]
                día = datoA[0][3]
                inicia = datoA[0][4]
                termina = datoA[0][5]
                aula = datoA[0][6]
                ayudante = datoA[0][7]
                self.creaMateria(materia, False, self.crea(Ayudante, ayudante),
                                 código, grupo, aula, inicia, termina, día, nivel, objCarrera)
            if(len(datoD) > 0):
                # print('docente '+str(datoD[0]))
                código = datoD[0][0]
                materia = datoD[0][1].strip()
                grupo = datoD[0][2]
                día = datoD[0][3]
                inicia = datoD[0][4]
                termina = datoD[0][5]
                aula = datoD[0][6]
                docente = datoD[0][7]

                self.creaMateria(materia, True, self.crea(Docente, docente),
                                 código, grupo, aula, inicia, termina, día, nivel, objCarrera)

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
        codGrup = código + '_' + grupo
        codNivelMateria = str(carrera.código) + '_' + código
        try:
            nivelMateria = NivelMateria.objects.get(código=codNivelMateria)
        except NivelMateria.DoesNotExist:
            nivelMateria = NivelMateria.objects.create(código=codNivelMateria, materia=mat, carrera=carrera, nivel=nivel)
            nivelMateria.save()
        try:
            grup = Grupo.objects.get(código=codGrup)
        except Grupo.DoesNotExist:
            grup = Grupo.objects.create(código=codGrup, materia=mat)
            grup.grupo = grupo
            grup.save()
        if(docente):
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
        ini = iniT[0] + ':' + iniT[1]
        finT = self.patronHora.findall(termina)[0]
        fin = finT[0] + ':' + finT[1]
        # ini = time.strptime(inicia, "%H%M")
        # fin = time.strptime(termina, "%H%M")
        try:
            hora = Horario.objects.get(código=codGrup + '_' + día)
        except Horario.DoesNotExist:
            hora = Horario.objects.create(código=codGrup + '_' + día, grupo=grup,
                                          aula=aul, inicio=ini, fin=fin, día=día)
            hora.save()
