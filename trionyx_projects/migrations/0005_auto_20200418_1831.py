# Generated by Django 2.2.6 on 2020-04-18 18:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('trionyx_projects', '0004_auto_20200418_1814'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='item',
            options={'permissions': (('add_item_limit', ' - Limit add'), ('change_item_limit', ' - Limit change'))},
        ),
    ]
