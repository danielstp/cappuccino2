# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-08 02:19
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('horario', '0006_horario_grupo'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='horario',
            name='id',
        ),
        migrations.AddField(
            model_name='horario',
            name='codigo',
            field=models.CharField(default=1, max_length=25, primary_key=True, serialize=False),
            preserve_default=False,
        ),
    ]
