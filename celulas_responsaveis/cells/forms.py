from django import forms

from celulas_responsaveis.cells.models import ApplicationSurvey


class ConsumerCellRegistrationForm(forms.Form):
    name = forms.CharField(label="Nome da Célula", max_length=100)

    description = forms.CharField(label="Informações adicionais", widget=forms.Textarea)
    address = forms.CharField(label="Endereço", max_length=100)
    neighborhood = forms.CharField(label="Bairro", max_length=50)
    city = forms.CharField(label="Cidade", max_length=50)
    state = forms.CharField(label="Estado", max_length=50)


class ApplicationForm(forms.Form):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        questions_form = ApplicationSurvey.objects.filter(is_active=True)

        if questions_form:
            form = questions_form[0]
            self.questions_instances = form.questions.all()

            for question in self.questions_instances:
                self.fields[question.name] = forms.CharField(max_length=255, required=True)
