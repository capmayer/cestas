import uuid as uuid
from django.db import models
from django.urls import reverse

from celulas_responsaveis.cells.models import ConsumerCell, ProducerCell
from celulas_responsaveis.users.models import User


class MonthCycle(models.Model):
    producer_cell = models.ForeignKey(ProducerCell, related_name="month_cycles", on_delete=models.CASCADE)
    begin = models.DateField()
    end = models.DateField()

    MONTH_CHOICES = (
        ("jan", "Janeiro"),
        ("fev", "Fevereiro"),
        ("mar", "Março"),
        ("abr", "Abril"),
        ("mai", "Maio"),
        ("jun", "Junho"),
        ("jul", "Julho"),
        ("ago", "Agosto"),
        ("set", "Setembro"),
        ("out", "Outubro"),
        ("nov", "Novembro"),
        ("dez", "Dezembro"),
    )

    name = models.CharField(max_length=3, choices=MONTH_CHOICES)

    def get_report_url(self):
        return reverse("producer:consumer_cell_week_cycle_detail", kwargs={"cell_slug": self.producer_cell.slug, "cycle_number": self.number})

    def get_additional_products_url(self):
        return reverse("producer:products_list_detail", kwargs={"cell_slug": self.producer_cell.slug, "cycle_number": self.number})

    def get_request_products_url(self):
        return reverse("baskets:additional_products_list", kwargs={"cell_slug": self.producer_cell.slug})

    def __str__(self) -> str:
        return f"Ciclo de {self.get_name_display()}"


class WeekCycle(models.Model):
    month_cycle = models.ForeignKey(MonthCycle, related_name="week_cycles", on_delete=models.CASCADE)
    delivery_day = models.DateField()
    request_day = models.DateField()
    number = models.IntegerField()

    def __str__(self) -> str:
        return f"Semana {self.number}"

class ProductsList(models.Model):
    producer_cell = models.ForeignKey(ProducerCell, related_name="product_list", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"Lista de produtos {self.producer_cell}"


class Basket(models.Model):
    person = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)
    week_cycle = models.ForeignKey(WeekCycle, related_name="baskets", on_delete=models.CASCADE)
    consumer_cell = models.ForeignKey(ConsumerCell, related_name="+", on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_date = models.DateField(auto_now_add=True)
    last_change = models.DateField(auto_now=True)

    total_price = models.FloatField(default=0)

    is_cancelled = models.BooleanField(default=False)
    is_paid = models.BooleanField(default=False)
    is_delivered = models.BooleanField(default=False)

    def __str__(self) -> str:
        return f"{self.person.name} - Valor: {self.total_price} - código: {self.uuid}"

    def get_absolute_url(self):
        return reverse("baskets:basket_detail", kwargs={"basket_uuid": self.uuid})


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
        self.available_quantity = self.available_quantity - value

        if self.available_quantity == 0.0:
            self.is_available = False
