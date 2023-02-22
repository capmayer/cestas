import datetime

from django import forms
from django.forms import formset_factory, inlineformset_factory, NumberInput

from celulas_responsaveis.baskets.models import AdditionalProductsList, ProductWithPrice


class SoldProductForm(forms.Form):
    name = forms.CharField(label="Produto", max_length=60, disabled=True)
    price = forms.FloatField(label="Preço", disabled=True)
    unit = forms.CharField(label="Unidade", max_length=10, disabled=True)
    requested_quantity = forms.FloatField(label="Quantidade", min_value=0, widget=NumberInput(attrs={"step": "0.1"}))


BasketFormSet = formset_factory(SoldProductForm, extra=0)

AdditionalProductsListFormSet = inlineformset_factory(AdditionalProductsList, ProductWithPrice, fields=("name", "price", "unit", "is_available",), extra=0)

class CycleForm(forms.Form):
    number = forms.CharField(label="Número")
    begin = forms.DateField(label="Início dia", initial=datetime.date.today)
    requests_end = forms.DateField(label="Pedidos até dia", initial=datetime.date.today() + datetime.timedelta(4))
    end = forms.DateField(label="Fim ciclo", initial=datetime.date.today() + datetime.timedelta(7))
