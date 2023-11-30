from django import forms


class DepositForm(forms.Form):
    value = forms.FloatField(label="Valor")
