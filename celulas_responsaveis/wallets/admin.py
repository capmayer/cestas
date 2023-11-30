from django.contrib import admin

from celulas_responsaveis.wallets.models import Wallet, Deposit


class WalletAdmin(admin.ModelAdmin):
    list_display = ['person', 'producer_cell', 'current_balance']
    actions = ["update_balance"]

    @admin.action(description="Atualizar saldo")
    def update_balance(self, request, queryset):
        for wallet in queryset:
            wallet.check_balance()
            wallet.save()

admin.site.register(Wallet, WalletAdmin)
admin.site.register(Deposit)
