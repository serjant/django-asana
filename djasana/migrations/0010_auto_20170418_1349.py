# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-18 17:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djasana', '0009_auto_20170418_1348'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='due_on',
            field=models.DateField(null=True),
        ),
    ]
