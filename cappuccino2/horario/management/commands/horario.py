import subprocess
import fileinput
import re
import requests
import datetime
import pycurl
import urllib.request
import os, datetime, time
import calendar
import pdfquery
import time

from django.utils import timezone
from cappuccino2.horario.models import Carrera, Docente, Ayudante, Aula, Grupo, Horario, Materia
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from parsel import Selector
from pdfquery import PDFQuery
from pdfquery.cache import FileCache

class Command(BaseCommand):
  help = 'Actualizar Horarios'
  patronCodigo = re.compile(r'^(\d+)\s+(.*)$')
  patronHora = re.compile(r'(\d{1,2})(\d{2})$')
  patronFecha = '%H:%M %d-%m-%Y'
  patronFechaApache = "%a, %d %b %Y %H:%M:%S %Z"

  def procesaPDF(self, url):
    text = requests.get(url).text
    pdf = PDFQuery(text)

  def handle(self, *args, **options):
    url = 'http://fcyt.umss.edu.bo/horarios/'
    text = requests.get(url).text
    selector = Selector(text=text)
    carreras    = selector.xpath('/html/body/table[4]//tr/td[3]/table//tr[2]/td'
                + '/table//tr/td/table//tr/td[2]/div/font/text()').extract()
    fechas      = selector.xpath('/html/body/table[4]//tr/td[3]/table//tr[2]/td'
                + '/table//tr/td/table//tr/td[4]/div/font/text()').extract()
    horariosPDF = selector.xpath('/html/body/table[4]//tr/td[3]/table//tr[2]/td'
                + '/table//tr/td/table//tr/td[3]/div/font/a/@href').extract()
    codigo = {}
    c = 0
    for carrera in carreras:
      tupla = self.patronCodigo.findall(carrera)
      codigo[tupla[0][0]]={}
      codigo[tupla[0][0]]['carrera']=tupla[0][1]
      codigo[tupla[0][0]]['fecha']=fechas[c]
      c=c+1

    patronPDF = re.compile(r'(\d+)\.pdf$')
    for pdf in horariosPDF:
      pdf1 = patronPDF.findall(pdf)
      codigo[pdf1[0]]['pdf']=pdf

    for carrera in codigo:
      self.stdout.write(self.style.SUCCESS('Carrera:"' + codigo[carrera]['carrera']+'"'))

      try:
        objCar = Carrera.objects.get(pk=carrera)
        self.stdout.write(self.style.WARNING('Existente' ))

        fecha = timezone.make_aware(datetime.datetime.strptime(codigo[carrera]['fecha'], self.patronFecha)
                 ,timezone=timezone.get_current_timezone())

        if(objCar.fecha<fecha):
          objCar.fecha=fecha
          objCar.nombre = codigo[carrera]['carrera']
          objCar.pdf = codigo[carrera]['pdf']
          objCar.save()
      except Carrera.DoesNotExist:
        self.stdout.write(self.style.WARNING('Nueva' ))
        objCar = Carrera.objects.create(codigo=carrera)
        objCar.nombre = codigo[carrera]['carrera']
        objCar.pdf = codigo[carrera]['pdf']
        objCar.save()
      self.descargar(carrera,objCar.codigo)
    self.stdout.write(self.style.SUCCESS('Terminado' ))

  def descargar(self, codigo, carrera):
    objCarrera = Carrera.objects.get(pk=carrera)
    u = urllib.request.urlopen(objCarrera.pdf)
    meta = u.info()
    fecha = timezone.make_aware(datetime.datetime.strptime(str(meta["Last-Modified"]), self.patronFechaApache)
             ,timezone=timezone.get_current_timezone())
    if(objCarrera.fechaPDF<fecha):
      self.stdout.write(self.style.WARNING('PDFNuevo' ))
      with open(settings.STATIC_ROOT+'/'+codigo+'.pdf', 'wb') as f:
        c = pycurl.Curl()
        c.setopt(c.URL, objCarrera.pdf)
        c.setopt(c.NOPROGRESS, False)
        c.setopt(c.XFERINFOFUNCTION, self.progress)
        c.setopt(c.WRITEDATA, f)
        c.perform()
        c.close()
      objCarrera.fechaPDF=fecha
      objCarrera.save()
      self.cosechar(settings.STATIC_ROOT+'/'+codigo,objCarrera)

  ## Callback function invoked when download/upload has progress
  def progress(self, download_t, download_d, upload_t, upload_d):
    if(download_t!=0):
      print( int(download_d*100/download_t),end='\r')


  def cosechar(self, ruta, objCarrera):
    expBase = '(\d{5,}) ([A-ZÑ. ]+) (\d{1,2})\s+([VISALUMIJ]{2}) (\d{3,4})-(\d{3,4})\((\d{3}[A-Z]?)\)\s+([A-ZÑ. ]+)'
    expA = re.compile(r'\(\*\) '+expBase)
    expD = re.compile(r'\s+'+expBase)
    base = ruta
    p = subprocess.run(['pdftotext', '-layout', '-nopgbrk', base+'.pdf'], stdout=subprocess.PIPE)
    p = subprocess.run(['sed', '-i', "s/¥/Ñ/g", base+'.txt'], stdout=subprocess.PIPE)

    for linea in fileinput.input(base+'.txt'):
        datoA = expA.findall(linea)
        datoD = expD.findall(linea)

        if(len(datoA)>0):
          #print('ayudante '+str(datoA[0]))
          codigo = datoA[0][0]
          materia = datoA[0][1].strip()
          grupo = datoA[0][2]
          día = datoA[0][3]
          inicia = datoA[0][4]
          termina = datoA[0][5]
          aula = datoA[0][6]
          ayudante = datoA[0][7]
          self.creaMateria(materia, False, self.crea(Ayudante, ayudante), codigo, grupo, aula, inicia, termina, día)
        if(len(datoD)>0):
          #print('docente '+str(datoD[0]))
          codigo = datoD[0][0]
          materia = datoD[0][1].strip()
          grupo = datoD[0][2]
          día = datoD[0][3]
          inicia = datoD[0][4]
          termina = datoD[0][5]
          aula = datoD[0][6]
          docente = datoD[0][7]

          self.creaMateria(materia,True, self.crea(Docente, docente), codigo, grupo, aula, inicia, termina, día)

  def crea(self, tipo, nombre):
    try:
      ayudante = tipo.objects.get(nombre=nombre)
    except tipo.DoesNotExist:
      ayudante = tipo.objects.create(nombre=nombre)
      ayudante.save()
    return ayudante

  def creaMateria(self, materia, docente, obj, codigo, grupo, aula, inicia, termina, día):
    try:
      mat = Materia.objects.get(nombre=materia)
    except Materia.DoesNotExist:
      mat = Materia.objects.create(nombre=materia,codigo=codigo)
      mat.save()
    codGrup=codigo+'_'+grupo
    try:
      grup = Grupo.objects.get(codigo=codGrup)
    except Grupo.DoesNotExist:
      grup = Grupo.objects.create(codigo=codGrup,materia=mat)
      grup.save()
    if(docente):
      grup.docente=obj
      grup.save()
    else:
      grup.ayudante=obj
      grup.save()
    try:
      aul = Aula.objects.get(codigo=aula)
    except Aula.DoesNotExist:
      aul = Aula.objects.create(codigo=aula)
      aul.save
    iniT = self.patronHora.findall(inicia)[0]
    ini = iniT[0]+':'+iniT[1]
    finT = self.patronHora.findall(termina)[0]
    fin = finT[0]+':'+finT[1]
    #ini = time.strptime(inicia, "%H%M")
    #fin = time.strptime(termina, "%H%M")
    try:
      hora = Horario.objects.get(codigo=codGrup+'_'+día)
    except Horario.DoesNotExist:
      hora = Horario.objects.create(codigo=codGrup+'_'+día, grupo=grup, aula=aul, inicio=ini, fin=fin)
      hora.save()
