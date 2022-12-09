from django import forms
from django.forms import formset_factory, inlineformset_factory

from celulas_responsaveis.baskets.models import AdditionalProductsList, ProductWithPrice


class SoldProductForm(forms.Form):
    name = forms.CharField(label="Produto", max_length=60, disabled=True)
    price = forms.FloatField(label="Preço", disabled=True)
    unit = forms.CharField(label="Unidade", max_length=10, disabled=True)
    requested_quantity = forms.FloatField(label="Quantidade")


BasketFormSet = formset_factory(SoldProductForm, extra=0)

AdditionalProductsListFormSet = inlineformset_factory(AdditionalProductsList, ProductWithPrice, fields=("name", "price", "unit", "is_available",), extra=0)
