# Generated by Django 4.0.8 on 2023-03-27 04:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('cells', '0001_initial'),
        ('baskets', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='cycle',
            name='consumer_cell',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consumer_cycles', to='cells.cell'),
        ),
        migrations.AddField(
            model_name='cycle',
            name='producer_cell',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='producer_cycles', to='cells.cell'),
        ),
        migrations.AddField(
            model_name='additionalproductslist',
            name='cycle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='additional_products_list', to='baskets.cycle'),
        ),
        migrations.AddField(
            model_name='additionalbasket',
            name='cycle',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='baskets', to='baskets.cycle'),
        ),
        migrations.AddField(
            model_name='additionalbasket',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]
