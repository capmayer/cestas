# Generated by Django 4.0.8 on 2023-10-31 22:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='viewing_as',
            field=models.CharField(choices=[('CS', 'Consumer'), ('PD', 'Producer')], default='CS', max_length=3),
        ),
    ]
