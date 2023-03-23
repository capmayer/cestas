from django.contrib import admin

from celulas_responsaveis.baskets.models import AdditionalBasket, Cycle, AdditionalProductsList, ProductWithPrice, \
    Product, SoldProduct, Unit

admin.site.register(AdditionalBasket)
admin.site.register(Cycle)
admin.site.register(AdditionalProductsList)
admin.site.register(Product)
admin.site.register(ProductWithPrice)
admin.site.register(SoldProduct)
admin.site.register(Unit)
