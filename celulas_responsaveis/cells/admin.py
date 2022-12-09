from django.contrib import admin

from celulas_responsaveis.cells.models import (
    ApplicationSurvey,
    ApplicationQuestion,
    ApplicationAnswer,
    Application,
    Cell, Membership, Role
)

# Register your models here.
admin.site.register(ApplicationSurvey)
admin.site.register(ApplicationQuestion)
admin.site.register(Application)
admin.site.register(ApplicationAnswer)
admin.site.register(Cell)
admin.site.register(Membership)
admin.site.register(Role)
