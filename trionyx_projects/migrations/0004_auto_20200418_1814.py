# Generated by Django 2.2.6 on 2020-04-18 18:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('trionyx_projects', '0003_auto_20200416_1411'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='item',
            options={'permissions': (('limited_change_item', 'Limited change'),)},
        ),
        migrations.AlterField(
            model_name='worklog',
            name='billed',
            field=models.FloatField(blank=True, help_text='On empty this wil be auto filled based on estimate and remaining billed hours, when there is no estimate billed will always be same as worked', null=True),
        ),
    ]