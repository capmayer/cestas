from django.contrib import admin

from celulas_responsaveis.cells.models import (
    ApplicationSurvey,
    ApplicationQuestion,
    ApplicationAnswer,
    Application,
    ConsumerCell,
    ProducerCell,
    Role,
    PaymentInfo,
    CellLocation,
    ConsumerMembership,
    ProducerMembership
)

# Register your models here.
admin.site.register(ApplicationSurvey)
admin.site.register(ApplicationQuestion)
admin.site.register(Application)
admin.site.register(ApplicationAnswer)
admin.site.register(ConsumerCell)
admin.site.register(CellLocation)
admin.site.register(ProducerCell)
admin.site.register(ConsumerMembership)
admin.site.register(Role)
admin.site.register(PaymentInfo)
admin.site.register(ProducerMembership)
