# Generated by Django 4.0.8 on 2023-02-22 01:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baskets', '0003_additionalbasket_total_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='cycle',
            name='end',
            field=models.DateField(default='2023-02-19'),
            preserve_default=False,
        ),
    ]
