from django.urls import path

from . import views

app_name = 'baskets'
urlpatterns = [
    path('cestas/', views.consumer_home, name='consumer_home'),
    path('pedido_realizado/<str:request_number>', views.basket_requested, name="basket_requested"),
    path('adicionais/', views.request_products, name="request_products"),
    path('cestas/<str:basket_number>/', views.basket_detail, name="basket_detail"),
    path('cestas/<str:basket_number>/alterar/', views.basket_detail_edit, name="basket_detail_edit"),
]
