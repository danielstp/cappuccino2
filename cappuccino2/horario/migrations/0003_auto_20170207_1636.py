# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-07 20:36
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horario', '0002_carrera_fecha'),
    ]

    operations = [
        migrations.AddField(
            model_name='carrera',
            name='fechaPDF',
            field=models.DateTimeField(default='2016-01-01 00:00:00-04'),
        ),
        migrations.AlterField(
            model_name='carrera',
            name='fecha',
            field=models.DateTimeField(default='2016-01-01 00:00:00-04'),
        ),
    ]
