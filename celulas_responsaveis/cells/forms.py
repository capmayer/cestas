from allauth.account.forms import SignupForm
from django import forms

from celulas_responsaveis.cells.models import ApplicationSurvey


class CellRegistrationForm(forms.Form):
    name = forms.CharField(label="Cell name", max_length=100)
    description = forms.CharField(widget=forms.Textarea)

    address = forms.CharField(label="Address", max_length=100)
    city = forms.CharField(label="City", max_length=50)
    state = forms.CharField(label="State", max_length=50)

    latitude = forms.DecimalField(max_digits=8, decimal_places=5)
    longitude = forms.DecimalField(max_digits=8, decimal_places=5)


class ApplicationForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        questions_form = ApplicationSurvey.objects.filter(is_active=True)

        if questions_form:
            form = questions_form[0]
            self.questions_instances = form.questions.all()

            for question in self.questions_instances:
                self.fields[question.name] = forms.CharField(max_length=255, required=True)
