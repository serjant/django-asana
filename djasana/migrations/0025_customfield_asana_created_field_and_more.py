# Generated by Django 5.1.7 on 2025-03-10 21:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('djasana', '0024_adds_custom_field_created_by'),
    ]

    operations = [
        migrations.AddField(
            model_name='customfield',
            name='asana_created_field',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customfield',
            name='default_access_level',
            field=models.CharField(blank=True, choices=[('admin', 'admin'), ('member', 'member'), ('commenter', 'commenter')], max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customfield',
            name='id_prefix',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customfield',
            name='is_formula_field',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='customfield',
            name='privacy_setting',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='customfield',
            name='representation_type',
            field=models.CharField(blank=True, choices=[('text', 'text'), ('enum', 'enum'), ('multi_enum', 'multi_enum'), ('number', 'number'), ('date', 'date'), ('people', 'people')], max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='attachment',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='customfield',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='customfieldsetting',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='project',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='projectstatus',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='story',
            name='hearts',
            field=models.ManyToManyField(related_name='%(class)s_hearted', to='djasana.user'),
        ),
        migrations.AlterField(
            model_name='story',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='synctoken',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='tag',
            name='color',
            field=models.CharField(blank=True, choices=[], max_length=16, null=True),
        ),
        migrations.AlterField(
            model_name='tag',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='task',
            name='hearts',
            field=models.ManyToManyField(related_name='%(class)s_hearted', to='djasana.user'),
        ),
        migrations.AlterField(
            model_name='task',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='team',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='user',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='webhook',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
        migrations.AlterField(
            model_name='workspace',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
