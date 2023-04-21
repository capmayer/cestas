from django.urls import path

from . import views

app_name = 'baskets'
urlpatterns = [
    path('', views.consumer_home, name='consumer_home'),
    path('pedido_realizado/<str:request_uuid>', views.basket_requested, name="basket_requested"),
    path('adicionais/', views.request_products, name="request_products"),
    path('<str:basket_uuid>/', views.basket_detail, name="basket_detail"),
]
