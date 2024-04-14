from django import forms


class DepositForm(forms.Form):
    value = forms.FloatField(label="Valor")
    payment_file = forms.FileField(
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
