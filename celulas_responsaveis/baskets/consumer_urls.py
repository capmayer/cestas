from django.urls import path

from . import views

app_name = 'baskets'
urlpatterns = [
    path('', views.home, name='home'),
    path('<str:cell_slug>/pedido_realizado/<str:request_uuid>', views.basket_requested, name="basket_requested"),
    path('<str:cell_slug>/adicionais/', views.additional_products_list, name="additional_products_list"),
]
