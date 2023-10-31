# Generated by Django 4.0.8 on 2023-10-30 23:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cells', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='consumercell',
            name='message_group_link',
            field=models.CharField(default='', max_length=120),
        ),
        migrations.AddField(
            model_name='consumercell',
            name='share_time',
            field=models.CharField(default='', max_length=30),
        ),
        migrations.AddField(
            model_name='consumercell',
            name='statute_file',
            field=models.FileField(blank=True, upload_to='cells_statute'),
        ),
    ]