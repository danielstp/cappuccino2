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
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(
        regex=r'^$',
        view=views.HorarioListView.as_view(),
        name='list'
    ),
    #    url(
    #        regex=r'^~redirect/$',
    #        view=views.UserRedirectView.as_view(),
    #        name='redirect'
    #    ),
    #    url(
    #        regex=r'^(?P<username>[\w.@+-]+)/$',
    #        view=views.UserDetailView.as_view(),
    #        name='detail'
    #    ),
    #    url(
    #        regex=r'^~update/$',
    #        view=views.UserUpdateView.as_view(),
    #        name='update'
    #    ),
]
