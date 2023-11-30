from django.contrib import admin

from celulas_responsaveis.baskets.models import Basket, MonthCycle, ProductsList, ProductWithPrice, \
    Product, SoldProduct, Unit, WeekCycle, CycleSettings


class BasketAdmin(admin.ModelAdmin):
    list_display = ["person", "consumer_cell", "week_cycle", "created_date", "total_price"]

admin.site.register(Basket, BasketAdmin)
admin.site.register(MonthCycle)
admin.site.register(ProductsList)
admin.site.register(Product)
admin.site.register(ProductWithPrice)
admin.site.register(SoldProduct)
admin.site.register(Unit)
admin.site.register(CycleSettings)
admin.site.register(WeekCycle)
