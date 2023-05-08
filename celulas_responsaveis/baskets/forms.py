import datetime

import numpy as np
from django import forms
from django.core.exceptions import ValidationError
from django.forms import formset_factory, inlineformset_factory, NumberInput, BaseFormSet, TextInput

from celulas_responsaveis.baskets.models import ProductsList, ProductWithPrice, Unit, MonthCycle


class SoldProductForm(forms.Form):
    name = forms.CharField(label="Produto", max_length=60, disabled=True)
    price = forms.FloatField(label="Preço", disabled=True)

    unit = forms.CharField(label="Unidade", disabled=True)
    requested_quantity = forms.CharField(
        label="Quantidade",
        widget=TextInput(
            attrs={
                "class": "form-control requested_quantity",
                "readonly": True,
            },
        ),
    )

    product_pk = forms.IntegerField(widget = forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        unit = kwargs['initial']['unit']
        requested_quantity_widget = self.fields['requested_quantity'].widget
        requested_quantity_widget.attrs["class"] += " text-center"
        requested_quantity_widget.attrs["step"] = unit.increment
        requested_quantity_widget.attrs["data-unit"] = unit.unit
        self.unit_name = unit.name
        self.unit_pk = unit.pk

    def clean_requested_quantity(self):
        from unidecode import unidecode
        import re
        requested_quantity = self.cleaned_data["requested_quantity"]
        requested_quantity = float(re.sub(r'[a-zA-Z]', '', unidecode(requested_quantity)))

        if requested_quantity <= 0.0:
            return requested_quantity

        product_with_price = ProductWithPrice.objects.get(pk=self.initial["product_pk"])
        available_quantity = product_with_price.available_quantity

        if product_with_price.unit.increment < 1:
            available_quantity = product_with_price.available_quantity * 1000

        if available_quantity >= requested_quantity:
            return requested_quantity

        raise ValidationError("Quantidade disponível insuficiente")

class BaseBasketFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        if all([form.cleaned_data.get('requested_quantity') <= 0 for form in self.forms]):
            raise ValidationError("Lista de pedidos vazia.")


BasketFormSet = formset_factory(SoldProductForm, extra=0, formset=BaseBasketFormSet)

class ProductWithPriceForm(forms.ModelForm):
    class Meta:
        model = ProductWithPrice
        fields = ["name", "price", "unit", "available_quantity"]
        labels = {
            "name": "Nome",
            "price": "Preço",
            "unit": "Medida",
            "available_quantity": "Quantidade",
        }

ProductsListFormSet = inlineformset_factory(
    parent_model=ProductsList,
    model=ProductWithPrice,
    form=ProductWithPriceForm,
    extra=1
)

class MonthCycleForm(forms.Form):
    begin = forms.DateField(label="Início do ciclo", initial=datetime.date.today().replace(day=1))


class WeekCycleForm(forms.Form):
    number = forms.CharField(label="Semana")
    request_day = forms.DateField(label="Fim dos pedidos", initial=datetime.date.today() + datetime.timedelta(3))
    delivery_day = forms.DateField(label="Dia de entrega", initial=datetime.date.today() + datetime.timedelta(5))
