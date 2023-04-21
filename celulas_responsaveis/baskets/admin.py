from django.contrib import admin

from celulas_responsaveis.baskets.models import Basket, MonthCycle, ProductsList, ProductWithPrice, \
    Product, SoldProduct, Unit, WeekCycle

admin.site.register(Basket)
admin.site.register(MonthCycle)
admin.site.register(ProductsList)
admin.site.register(Product)
admin.site.register(ProductWithPrice)
admin.site.register(SoldProduct)
admin.site.register(Unit)
admin.site.register(WeekCycle)
