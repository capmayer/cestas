import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.forms import formset_factory, inlineformset_factory, NumberInput, BaseFormSet

from celulas_responsaveis.baskets.models import AdditionalProductsList, ProductWithPrice, Unit


class SoldProductForm(forms.Form):
    name = forms.CharField(label="Produto", max_length=60, disabled=True)
    price = forms.FloatField(label="Preço", disabled=True)

    unit = forms.CharField(label="Unidade", disabled=True)
    requested_quantity = forms.FloatField(label="Quantidade", min_value=0, widget=NumberInput(attrs={"step": "0.1", "class": "form-control requested_quantity"}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        unit = kwargs['initial']['unit']
        requested_quantity_widget = self.fields['requested_quantity'].widget
        requested_quantity_widget.attrs['step'] = unit.increment

        if unit.increment >= 1:
            requested_quantity_widget.attrs["onkeypress"] = "return validateInteger(event)"
        else:
            requested_quantity_widget.attrs["onkeypress"] = "return validateFloat(event)"


class BaseBasketFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        if all([form.cleaned_data.get('requested_quantity') == 0 for form in self.forms]):
            raise ValidationError("Lista de pedidos vazia.")


BasketFormSet = formset_factory(SoldProductForm, extra=0, formset=BaseBasketFormSet)

AdditionalProductsListFormSet = inlineformset_factory(AdditionalProductsList, ProductWithPrice, fields=("name", "price", "unit", "is_available",), extra=1)

class CycleForm(forms.Form):
    number = forms.CharField(label="Número")
    begin = forms.DateField(label="Início dia", initial=datetime.date.today)
    requests_end = forms.DateField(label="Pedidos até dia", initial=datetime.date.today() + datetime.timedelta(4))
    end = forms.DateField(label="Fim ciclo", initial=datetime.date.today() + datetime.timedelta(7))
