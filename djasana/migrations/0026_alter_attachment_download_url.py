# Generated by Django 5.1.7 on 2025-03-10 21:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djasana', '0025_customfield_asana_created_field_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='download_url',
            field=models.URLField(blank=True, max_length=5120, null=True),
        ),
    ]
