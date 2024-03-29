# Generated by Django 4.0.8 on 2023-04-29 23:27

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('users', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Application',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created', models.DateField(auto_now_add=True)),
                ('is_pending', models.BooleanField(default=True)),
                ('approved', models.BooleanField(default=False)),
                ('approved_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ApplicationSurvey',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('is_active', models.BooleanField(default=True)),
                ('created', models.DateField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='ConsumerCell',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=False)),
                ('created', models.DateField(auto_now_add=True)),
                ('slug', models.SlugField(max_length=120)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='ProducerCell',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('description', models.TextField()),
                ('is_active', models.BooleanField(default=False)),
                ('created', models.DateField(auto_now_add=True)),
                ('slug', models.SlugField(max_length=120)),
            ],
            options={
                'ordering': ['-created'],
            },
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
            ],
        ),
        migrations.CreateModel(
            name='ProducerMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('join_date', models.DateField(auto_now_add=True)),
                ('cell', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='cells.producercell')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('role', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='cells.role')),
            ],
        ),
        migrations.AddField(
            model_name='producercell',
            name='members',
            field=models.ManyToManyField(through='cells.ProducerMembership', to=settings.AUTH_USER_MODEL),
        ),
        migrations.CreateModel(
            name='PaymentInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.TextField()),
                ('receiver_name', models.CharField(max_length=50)),
                ('receiver_contact', models.CharField(max_length=20)),
                ('pix_key', models.CharField(max_length=50)),
                ('producer_cell', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payment_info', to='cells.producercell')),
            ],
        ),
        migrations.CreateModel(
            name='ConsumerMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=True)),
                ('join_date', models.DateField(auto_now_add=True)),
                ('cell', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='cells.consumercell')),
                ('person', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('role', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='cells.role')),
            ],
        ),
        migrations.AddField(
            model_name='consumercell',
            name='members',
            field=models.ManyToManyField(through='cells.ConsumerMembership', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='consumercell',
            name='producer_cell',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='consumer_cells', to='cells.producercell'),
        ),
        migrations.CreateModel(
            name='CellLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('address', models.CharField(max_length=100)),
                ('neighborhood', models.CharField(max_length=50)),
                ('city', models.CharField(max_length=50)),
                ('state', models.CharField(max_length=50)),
                ('latitude', models.DecimalField(decimal_places=5, default=0, max_digits=8)),
                ('longitude', models.DecimalField(decimal_places=5, default=0, max_digits=8)),
                ('cell', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='location', to='cells.consumercell')),
            ],
        ),
        migrations.CreateModel(
            name='ApplicationQuestion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('application_survey', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='questions', to='cells.applicationsurvey')),
            ],
        ),
        migrations.CreateModel(
            name='ApplicationAnswer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('answer', models.CharField(max_length=255)),
                ('application', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='survey_answers', to='cells.application')),
                ('question', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='cells.applicationquestion')),
            ],
        ),
        migrations.AddField(
            model_name='application',
            name='cell',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='cells.consumercell'),
        ),
        migrations.AddField(
            model_name='application',
            name='person',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]
