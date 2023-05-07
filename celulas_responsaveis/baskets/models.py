import datetime
import locale
import random

from django.contrib.sites.models import Site
from django.db import models
from django.urls import reverse

from celulas_responsaveis.cells.models import ConsumerCell, ProducerCell
from celulas_responsaveis.users.models import User


class CycleSettings(models.Model):
    producer_cell = models.ForeignKey(ProducerCell, related_name="cycle_settings", on_delete=models.CASCADE)
    week_day_requests_end = models.IntegerField()
    week_day_delivery = models.IntegerField()

def hex_uuid():
    pass

MONTH_TO_PORTUGUESE = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]

class MonthCycle(models.Model):
    producer_cell = models.ForeignKey(ProducerCell, related_name="month_cycles", on_delete=models.CASCADE)
    begin = models.DateField()

    def get_report_url(self):
        return reverse("producer:consumer_cell_week_cycle_detail", kwargs={"cell_slug": self.producer_cell.slug, "cycle_number": self.number})

    def get_additional_products_url(self):
        return reverse("producer:products_list_detail", kwargs={"cell_slug": self.producer_cell.slug, "cycle_number": self.number})

    def get_request_products_url(self):
        return reverse("baskets:additional_products_list", kwargs={"cell_slug": self.producer_cell.slug})

    def get_month_number(self):
        return self.begin.month

    def get_identifier(self):
        return self.begin.strftime('%m%Y')

    def __str__(self) -> str:
        return f"Ciclo de {MONTH_TO_PORTUGUESE[self.begin.month - 1]}"


class WeekCycle(models.Model):
    month_cycle = models.ForeignKey(MonthCycle, related_name="week_cycles", on_delete=models.CASCADE)
    delivery_day = models.DateField()
    request_day = models.DateField()
    number = models.IntegerField()

    def get_number_of_baskets(self):
        return self.baskets.count()

    def get_number_of_paid_baskets(self):
        return self.baskets.filter(is_paid=True).count()

    def get_number_of_cells(self):
        return self.month_cycle.producer_cell.consumer_cells.count()

    def __str__(self) -> str:
        return f"Semana {self.number}"

class ProductsList(models.Model):
    producer_cell = models.ForeignKey(ProducerCell, related_name="product_list", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"Lista de produtos {self.producer_cell}"

def basket_identification_number():
    time_now = datetime.datetime.now()
    random_number = random.randrange(0, 10**6)
    identification = f"{time_now.day:02d}{time_now.month:02d}{time_now.year:04d}{random_number:06d}"
    return identification

class Basket(models.Model):
    """
    Representa uma cesta de pedidos adicionais.
    """
    person = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)
    week_cycle = models.ForeignKey(WeekCycle, related_name="baskets", on_delete=models.CASCADE)
    consumer_cell = models.ForeignKey(ConsumerCell, related_name="+", on_delete=models.CASCADE)
    number = models.CharField(default=basket_identification_number, editable=False, unique=True, max_length=20)
    created_date = models.DateTimeField(auto_now_add=True)
    last_change = models.DateTimeField(auto_now=True)

    total_price = models.FloatField(default=0)

    is_cancelled = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.person.name} - Valor: {self.total_price} - código: {self.number}"

    def get_absolute_url(self):
        return reverse("baskets:basket_detail", kwargs={"basket_number": self.number})

class Product(models.Model):
    name = models.CharField(max_length=60)

    def __str__(self) -> str:
        return f"{self.name}"


class Unit(models.Model):
    """
    Unit define as unidades disponíveis no sistema e como será o incremento delas.

    name: Nome que aparece para o usuário.
    increment: Valor de acrescimo/decrescimo ao clicar nas setas.
    unit: Medida

    Exemplos: Unit(Kilograma, 0.1, Kg) permite que o usuário selecione de 100 em 100 gramas do produto.
              Unit(Unidade, 1, Und) permite que o usuário selecione de 1 em 1 unidade do produto.
    """

    name = models.CharField(max_length=15)
    increment = models.FloatField(default=1.0)
    k_unit = models.CharField(max_length=15, default="")
    unit = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.name}"


class SoldProduct(models.Model):
    product = models.ForeignKey(Product, related_name="+", null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=60)
    unit = models.ForeignKey(Unit, related_name="+", null=True, on_delete=models.SET_NULL)
    price = models.FloatField()
    requested_quantity = models.FloatField()

    basket = models.ForeignKey(Basket, related_name="products", on_delete=models.CASCADE)

    @property
    def total_price(self) -> float:
        return self.price * self.requested_quantity

    def __str__(self) -> str:
        return f"{self.requested_quantity}{self.unit} de {self.product} = {self.total_price}"


class ProductWithPrice(models.Model):
    product = models.ForeignKey(Product, related_name="+", null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=60)
    unit = models.ForeignKey(Unit, related_name="+", null=True, on_delete=models.SET_NULL)
    price = models.FloatField()

    available_quantity = models.FloatField()
    is_available = models.BooleanField(default=True)

    additional_products_list = models.ForeignKey(ProductsList, related_name="products", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.name}"

    def reduce_available_quantity(self, value):
        if self.unit.increment < 1:
            value = value / 1000


        self.available_quantity = self.available_quantity - value

        if self.available_quantity == 0.0:
            self.is_available = False
