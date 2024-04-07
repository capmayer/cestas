from django.contrib import admin

from celulas_responsaveis.baskets.models import Basket, MonthCycle, ProductsList, ProductWithPrice, \
    Product, SoldProduct, Unit, WeekCycle, CycleSettings, OfferedBasketType, ConsumerBasketTypeChoice, MonthlyConsumer
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


class MonthCycleAdmin(admin.ModelAdmin):
    list_display = ["producer_cell", "begin", "number_of_weeks"]


class ProductsListAdmin(admin.ModelAdmin):
    list_display = ["producer_cell"]


class ProductWithPriceAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "unit", "available_quantity", "is_available", "additional_products_list"]


class SoldProductAdmin(admin.ModelAdmin):
    list_display = ["name", "product", "price", "unit", "requested_quantity", "basket"]


class WeekCycleAdmin(admin.ModelAdmin):
    list_display = ["month_cycle", "delivery_day", "request_day", "number"]


class OfferedBasketTypeAdmin(admin.ModelAdmin):
    list_display = ["producer_cell", "name", "price", "average_weight", "number_of_products"]


class ConsumerBasketTypeChoiceAdmin(admin.ModelAdmin):
    list_display = ["person", "consumer_cell", "offered_basket_type", "period"]



class MonthlyConsumerAdmin(admin.ModelAdmin):
    list_display = ["month_cycle", "person", "number", "consumer_cell", "consumer_basket_choice", "wallet", "total_price", "created_date"]



admin.site.register(Basket, BasketAdmin)
admin.site.register(MonthCycle, MonthCycleAdmin)
admin.site.register(ProductsList, ProductsListAdmin)
admin.site.register(Product)
admin.site.register(ProductWithPrice, ProductWithPriceAdmin)
admin.site.register(SoldProduct, SoldProductAdmin)
admin.site.register(Unit)
admin.site.register(CycleSettings)
admin.site.register(WeekCycle, WeekCycleAdmin)
admin.site.register(OfferedBasketType, OfferedBasketTypeAdmin)
admin.site.register(ConsumerBasketTypeChoice, ConsumerBasketTypeChoiceAdmin)
admin.site.register(MonthlyConsumer, MonthlyConsumerAdmin)
