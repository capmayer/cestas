# Generated by Django 4.0.8 on 2023-03-27 05:10

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AdditionalBasket',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_date', models.DateField(auto_now_add=True)),
                ('last_change', models.DateField(auto_now=True)),
                ('total_price', models.FloatField(default=0)),
                ('is_cancelled', models.BooleanField(default=False)),
                ('is_paid', models.BooleanField(default=False)),
                ('is_delivered', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='AdditionalProductsList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ],
        ),
        migrations.CreateModel(
            name='Cycle',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.IntegerField()),
                ('begin', models.DateField()),
                ('end', models.DateField()),
                ('requests_end', models.DateField()),
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
            name='Unit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=15)),
                ('increment', models.FloatField(default=1.0)),
                ('unit', models.CharField(max_length=15)),
            ],
        ),
        migrations.CreateModel(
            name='SoldProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=60)),
                ('price', models.FloatField()),
                ('requested_quantity', models.FloatField()),
                ('basket', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='baskets.additionalbasket')),
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
                ('is_available', models.BooleanField(default=True)),
                ('additional_products_list', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='products', to='baskets.additionalproductslist')),
                ('product', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='baskets.product')),
                ('unit', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='baskets.unit')),
            ],
        ),
    ]
