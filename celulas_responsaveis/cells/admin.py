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
    ProducerMembership, ProducerCellSettings
)


class ConsumerMembershipAdmin(admin.ModelAdmin):
    list_display = ['person', 'cell', 'role', 'join_date']
    actions = ["new_wallet"]

    @admin.action(description="Criar caderneta")
    def new_wallet(self, request, queryset):
        def create_wallet():
            new_wallet = Wallet()
            new_wallet.consumer_membership = membership
            new_wallet.producer_cell = membership.cell.producer_cell
            new_wallet.person = membership.person

            new_wallet.save()

        from celulas_responsaveis.wallets.models import Wallet

        for membership in queryset:
            if not membership.wallet.exists():
                create_wallet()

            # If producer cell of consumer cell changed, then we create a new wallet for this relation.
            if membership.wallet.exists():
                wallet = membership.wallet.last()

                if wallet.producer_cell != membership.cell.producer_cell:
                    create_wallet()


class ProducerCellAdmin(admin.ModelAdmin):
    list_display = ["name"]
    actions = ["create_settings"]

    @admin.action(description="Create settings for cell")
    def create_settings(self, request, queryset):
        for cell in queryset:
            cell_settings = ProducerCellSettings.objects.filter(cell=cell)

            if not cell_settings.exists():
                cell_settings = ProducerCellSettings()
                cell_settings.cell = cell
                cell_settings.save()

class PaymentInfoAdmin(admin.ModelAdmin):
    list_display = ["producer_cell", "receiver_name", "pix_key"]


class ProducerMembershipAdmin(admin.ModelAdmin):
    list_display = ["cell", "person", "role", "is_active", "join_date"]


class ConsumerCellAdmin(admin.ModelAdmin):
    list_display = ["name", "share_day", "share_time", "statute_file", "producer_cell"]


class ProducerCellSettingsAdmin(admin.ModelAdmin):
    list_display = ["cell", "buy_only_in_month_cycle", "biweekly_baskets"]


# Register your models here.
admin.site.register(ApplicationSurvey)
admin.site.register(ApplicationQuestion)
admin.site.register(Application)
admin.site.register(ApplicationAnswer)
admin.site.register(ConsumerCell, ConsumerCellAdmin)
admin.site.register(CellLocation)
admin.site.register(ProducerCell, ProducerCellAdmin)
admin.site.register(ConsumerMembership, ConsumerMembershipAdmin)
admin.site.register(Role)
admin.site.register(PaymentInfo, PaymentInfoAdmin)
admin.site.register(ProducerMembership, ProducerMembershipAdmin)
admin.site.register(ProducerCellSettings, ProducerCellSettingsAdmin)
