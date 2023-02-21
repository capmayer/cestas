import uuid as uuid
from django.db import models
from django.urls import reverse

from celulas_responsaveis.cells.models import Cell
from celulas_responsaveis.users.models import User


class Cycle(models.Model):
    cell = models.ForeignKey(Cell, related_name="cycles", on_delete=models.CASCADE)
    number = models.IntegerField()
    begin = models.DateField()
    requests_end = models.DateField()

    def get_detail_url(self):
        return reverse("baskets:cycle_report_detail", kwargs={"cell_slug": self.cell.slug, "cycle_number": self.number})

    def get_additional_products_url(self):
        return reverse("baskets:additional_products_detail", kwargs={"cell_slug": self.cell.slug, "cycle_number": self.number})

    def get_request_products_url(self):
        return reverse("baskets:additional_products_list", kwargs={"cell_slug": self.cell.slug})

    def __str__(self) -> str:
        return f"Ciclo #{self.number}"


class AdditionalProductsList(models.Model):
    cycle = models.ForeignKey(Cycle, related_name="additional_products_list", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.cycle} da {self.cycle.cell}"


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


class SoldProduct(models.Model):
    product = models.ForeignKey(Product, related_name="+", null=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=60)
    unit = models.CharField(max_length=10)
    price = models.FloatField()
    requested_quantity = models.FloatField()

    basket = models.ForeignKey(AdditionalBasket, related_name="products", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.requested_quantity}{self.unit} de {self.product} = {self.price * self.requested_quantity}"


class ProductWithPrice(models.Model):
    product = models.ForeignKey(Product, related_name="+", null=True, on_delete=models.SET_NULL)
    name = models.CharField(max_length=60)
    unit = models.CharField(max_length=10)
    price = models.FloatField()
    is_available = models.BooleanField(default=True)

    additional_products_list = models.ForeignKey(AdditionalProductsList, related_name="products", on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f"{self.product}"
