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


class ConsumerMembershipAdmin(admin.ModelAdmin):
    list_display = ['person', 'cell', 'role', 'join_date']
    actions = ["create_wallet"]

    @admin.action(description="Criar caderneta")
    def create_wallet(self, request, queryset):
        from celulas_responsaveis.wallets.models import Wallet

        for membership in queryset:
            if not membership.wallet.exists():
                new_wallet = Wallet()
                new_wallet.consumer_membership = membership
                new_wallet.producer_cell = membership.cell.producer_cell
                new_wallet.person = membership.person

                new_wallet.save()

# Register your models here.
admin.site.register(ApplicationSurvey)
admin.site.register(ApplicationQuestion)
admin.site.register(Application)
admin.site.register(ApplicationAnswer)
admin.site.register(ConsumerCell)
admin.site.register(CellLocation)
admin.site.register(ProducerCell)
admin.site.register(ConsumerMembership, ConsumerMembershipAdmin)
admin.site.register(Role)
admin.site.register(PaymentInfo)
admin.site.register(ProducerMembership)
