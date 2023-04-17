# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from .. import urls as urlsRoot
from . import views

router = urlsRoot.router
router.register(r"carreras", views.CarreraViewSet)
router.register(r"materias", views.MateriaViewSet)
router.register(r"nivel", views.NivelMateriaViewSet)
router.register(r"actualización", views.ActualizaciónViewSet)
router.register(r"docente", views.DocenteViewSet)
router.register(r"ayudante", views.AyudanteViewSet)
router.register(r"aula", views.AulaViewSet)
router.register(r"grupo", views.GrupoViewSet)
router.register(r"horario", views.HorarioViewSet)
