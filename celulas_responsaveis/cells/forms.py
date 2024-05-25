from django import forms
from django.forms import TextInput

from celulas_responsaveis.cells.models import ApplicationSurvey, ProducerCellSettings, ConsumerMembership, Application, \
    ApplicationAnswer


class ConsumerCellRegistrationForm(forms.Form):
    name = forms.CharField(label="Nome da Célula", max_length=100)

    description = forms.CharField(label="Informações adicionais", widget=forms.Textarea)
    address = forms.CharField(label="Endereço", max_length=100)
    neighborhood = forms.CharField(label="Bairro", max_length=50)
    city = forms.CharField(label="Cidade", max_length=50)
    state = forms.CharField(label="Estado", max_length=50)


class ApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.survey_answers.all():
            self.answer_instances = self.instance.survey_answers.all()

            for answer in self.answer_instances:
                self.fields[answer.question.name] = forms.CharField(
                    max_length=255,
                    required=True,
                    widget=TextInput(
                        attrs={
                            "class": "h4",
                        },
                    ),
                    initial=answer.answer,
                )

        else:
            if survey := ApplicationSurvey.objects.filter(is_active=True).last():
                self.questions_instances = survey.questions.all()

                for question in self.questions_instances:
                    self.fields[question.name] = forms.CharField(
                        max_length=255,
                        required=True,
                        widget=TextInput(
                            attrs={
                                "class": "h4",
                            },
                        ),
                    )


class ProducerCellSettingsForm(forms.ModelForm):
    class Meta:
        model = ProducerCellSettings
        fields = ["buy_only_in_month_cycle", "biweekly_baskets"]
        labels = {
            "buy_only_in_month_cycle": "Pedidos adicionais apenas para participantes do ciclo",
            "biweekly_baskets": "Adquirir cestas quinzenais."
        }

class ConsumerMembershipForm(forms.ModelForm):
    class Meta:
        model = ConsumerMembership
        fields = ["is_active"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["is_active"].widget = forms.HiddenInput()
