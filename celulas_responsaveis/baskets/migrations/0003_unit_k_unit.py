# Generated by Django 4.0.8 on 2023-05-06 00:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baskets', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='k_unit',
            field=models.CharField(default='', max_length=15),
        ),
    ]
