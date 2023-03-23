import uuid as uuid
from django.db import models
from django.urls import reverse

from celulas_responsaveis.cells.models import Cell
from celulas_responsaveis.users.models import User


class Cycle(models.Model):
    consumer_cell = models.ForeignKey(Cell, related_name="consumer_cycles", on_delete=models.CASCADE)
    producer_cell = models.ForeignKey(Cell, related_name="producer_cycles", on_delete=models.CASCADE)
    number = models.IntegerField()
    begin = models.DateField()
    end = models.DateField()
    requests_end = models.DateField()

    def get_report_url(self):
        return reverse("producer:cycle_report_detail", kwargs={"cell_slug": self.consumer_cell.slug, "cycle_number": self.number})

    def get_additional_products_url(self):
        return reverse("producer:additional_products_detail", kwargs={"cell_slug": self.consumer_cell.slug, "cycle_number": self.number})

    def get_request_products_url(self):
        return reverse("baskets:additional_products_list", kwargs={"cell_slug": self.consumer_cell.slug})

    def __str__(self) -> str:
        return f"Ciclo #{self.number} da {self.consumer_cell}"


class AdditionalProductsList(models.Model):
    cycle = models.ForeignKey(Cycle, related_name="additional_products_list", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"Lista de adicionais {self.cycle}"


class AdditionalBasket(models.Model):
    person = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)
    cycle = models.ForeignKey(Cycle, related_name="baskets", on_delete=models.CASCADE)
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
    name = models.CharField(max_length=15)
    increment = models.FloatField(default=1.0)

    def __str__(self):
        return f"{self.name}"


class SoldProduct(models.Model):
    product = models.ForeignKey(Product, related_name="+", null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=60)
    unit = models.ForeignKey(Unit, related_name="+", null=True, on_delete=models.SET_NULL)
    price = models.FloatField()
    requested_quantity = models.FloatField()

    basket = models.ForeignKey(AdditionalBasket, related_name="products", on_delete=models.CASCADE)

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
    is_available = models.BooleanField(default=True)

    additional_products_list = models.ForeignKey(AdditionalProductsList, related_name="products", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.name}"
