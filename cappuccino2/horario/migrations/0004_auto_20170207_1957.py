# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-07 23:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('horario', '0003_auto_20170207_1636'),
    ]

    operations = [
        migrations.CreateModel(
            name='Aula',
            fields=[
                ('codigo', models.CharField(max_length=25, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Ayudante',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Docente',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
            ],
        ),
        migrations.CreateModel(
            name='Grupo',
            fields=[
                ('codigo', models.CharField(max_length=25, primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Horario',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('día', models.CharField(choices=[('1', 'LU'), ('2', 'MA'), ('3', 'MI'),
                                                  ('4', 'JU'), ('5', 'VI'), ('6', 'SA'), ('7', 'DO')], max_length=2)),
                ('inicio', models.TimeField()),
                ('fin', models.TimeField()),
            ],
        ),
        migrations.CreateModel(
            name='Materia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=255)),
            ],
        ),
        migrations.AddField(
            model_name='grupo',
            name='materia',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='horario.Materia'),
        ),
    ]
