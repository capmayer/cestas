from django.urls import path

from . import views

app_name = 'baskets'
urlpatterns = [
    path('', views.home, name='home_consumer'),
    path('<str:cell_slug>/pedido_realizado/<str:request_uuid>', views.basket_requested, name="basket_requested"),
    path('<str:cell_slug>/adicionais/', views.additional_products_list, name="additional_products_list"),
    path('<str:basket_uuid>/', views.additional_basket_detail, name="basket_detail"),
]
