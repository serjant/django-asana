# Generated by Django 5.1.7 on 2025-03-10 23:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djasana', '0027_projectstatus_author_projectstatus_modified_at'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customfield',
            name='description',
            field=models.CharField(blank=True, max_length=8192, null=True),
        ),
    ]
