# Generated by Django 4.0.8 on 2023-02-21 00:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baskets', '0002_additionalbasket_additionalproductslist_cycle_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='additionalbasket',
            name='total_price',
            field=models.FloatField(default=0),
        ),
    ]