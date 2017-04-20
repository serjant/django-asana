# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-18 14:33
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djasana', '0002_auto_20170418_0941'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='workspaces',
            field=models.ManyToManyField(to='djasana.Workspace'),
        ),
        migrations.AlterField(
            model_name='team',
            name='organization_id',
            field=models.IntegerField(null=True),
        ),
    ]
