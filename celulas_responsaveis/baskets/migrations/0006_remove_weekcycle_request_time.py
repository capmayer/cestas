# Generated by Django 4.0.8 on 2023-06-02 00:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('baskets', '0005_alter_weekcycle_request_day'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='weekcycle',
            name='request_time',
        ),
    ]
