# Generated by Django 4.0.8 on 2023-04-29 23:27

import celulas_responsaveis.baskets.models
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Basket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.CharField(default=celulas_responsaveis.baskets.models.basket_identification_number, editable=False, max_length=20, unique=True)),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('last_change', models.DateTimeField(auto_now=True)),
                ('total_price', models.FloatField(default=0)),
                ('is_cancelled', models.BooleanField(default=False)),
                ('is_paid', models.BooleanField(default=False)),
                ('is_delivered', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='CycleSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_day_requests_end', models.IntegerField()),
                ('week_day_delivery', models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name='MonthCycle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('begin', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
            ],
        ),
        migrations.CreateModel(
            name='ProductsList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=15)),
                ('increment', models.FloatField(default=1.0)),
                ('unit', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='WeekCycle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('delivery_day', models.DateField()),
                ('request_day', models.DateField()),
                ('number', models.IntegerField()),
                ('month_cycle', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='week_cycles', to='baskets.monthcycle')),
            ],
        ),
        migrations.CreateModel(
            name='SoldProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('price', models.FloatField()),
                ('requested_quantity', models.FloatField()),
                ('basket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='baskets.basket')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='baskets.product')),
                ('unit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='baskets.unit')),
            ],
        ),
        migrations.CreateModel(
            name='ProductWithPrice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('price', models.FloatField()),
                ('available_quantity', models.FloatField()),
                ('is_available', models.BooleanField(default=True)),
                ('additional_products_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='baskets.productslist')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='baskets.product')),
                ('unit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='baskets.unit')),
            ],
        ),
    ]
