from django.contrib import admin

from celulas_responsaveis.baskets.models import Basket, MonthCycle, ProductsList, ProductWithPrice, \
    Product, SoldProduct, Unit, WeekCycle, CycleSettings
from celulas_responsaveis.cells.models import ConsumerMembership


class BasketAdmin(admin.ModelAdmin):
    list_display = ["person", "consumer_cell", "week_cycle", "created_date", "total_price"]

    actions = ["update_wallet"]

    @admin.action(description="Atualizar caderneta da cesta")
    def update_wallet(self, request, queryset):
        from celulas_responsaveis.wallets.models import Wallet

        for basket in queryset:
            if basket.wallet is None:
                consumer_membership = ConsumerMembership.objects.get(person=basket.person, cell=basket.consumer_cell)
                wallet = Wallet.objects.get(person=basket.person, consumer_membership=consumer_membership, producer_cell=basket.consumer_cell.producer_cell)

                basket.wallet = wallet
                basket.save()

admin.site.register(Basket, BasketAdmin)
admin.site.register(MonthCycle)
admin.site.register(ProductsList)
admin.site.register(Product)
admin.site.register(ProductWithPrice)
admin.site.register(SoldProduct)
admin.site.register(Unit)
admin.site.register(CycleSettings)
admin.site.register(WeekCycle)
