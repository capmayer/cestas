import datetime

from django import forms
from django.core.exceptions import ValidationError
from django.forms import formset_factory, inlineformset_factory, NumberInput, BaseFormSet

from celulas_responsaveis.baskets.models import ProductsList, ProductWithPrice, Unit, MonthCycle


class SoldProductForm(forms.Form):
    name = forms.CharField(label="Produto", max_length=60, disabled=True)
    price = forms.FloatField(label="Preço", disabled=True)

    unit = forms.CharField(label="Unidade", disabled=True)
    requested_quantity = forms.FloatField(
        label="Quantidade",
        min_value=0,
        widget=NumberInput(
            attrs={
                "step": "0.1",
                "class": "form-control requested_quantity"}
        )
    )

    product_pk = forms.IntegerField(widget = forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        unit = kwargs['initial']['unit']
        requested_quantity_widget = self.fields['requested_quantity'].widget
        requested_quantity_widget.attrs['step'] = unit.increment

        if unit.increment >= 1:
            requested_quantity_widget.attrs["onkeypress"] = "return validateInteger(event)"
        else:
            requested_quantity_widget.attrs["onkeypress"] = "return validateFloat(event)"

    def clean_requested_quantity(self):
        requested_quantity = self.cleaned_data["requested_quantity"]

        if requested_quantity <= 0.0:
            return requested_quantity

        product_with_price = ProductWithPrice.objects.get(pk=self.initial["product_pk"])

        if product_with_price.available_quantity >= requested_quantity:
            return requested_quantity

        raise ValidationError("Produto em falta.")

class BaseBasketFormSet(BaseFormSet):
    def clean(self):

        if any(self.errors):
            return

        if all([form.cleaned_data.get('requested_quantity') == 0 for form in self.forms]):
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
    name = forms.ChoiceField(label="Mês", choices=MonthCycle.MONTH_CHOICES)
    begin = forms.DateField(label="Início do ciclo", initial=datetime.date.today().replace(day=1))
    end = forms.DateField(label="Fim do ciclo")


class WeekCycleForm(forms.Form):
    number = forms.CharField(label="Semana")
    request_day = forms.DateField(label="Fim dos pedidos", initial=datetime.date.today() + datetime.timedelta(3))
    delivery_day = forms.DateField(label="Dia de entrega", initial=datetime.date.today() + datetime.timedelta(5))
