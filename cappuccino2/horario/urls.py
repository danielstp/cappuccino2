# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf.urls import url, include
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r'carreras', views.CarreraViewSet)
router.register(r'materias', views.MateriaViewSet)
router.register(r'nivel', views.NivelMateriaViewSet)


urlpatterns = [
    url(r'^', include(router.urls)),
    url(
        regex=r'^$',
        view=views.HorarioListView.as_view(),
        name='list'
    ),
]
