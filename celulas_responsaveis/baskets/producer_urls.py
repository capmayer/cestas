from django.urls import path

from . import views

app_name = 'producer'
urlpatterns = [
    path('produtores/', views.producer_home, name="producer_home"),
    path('produtores/ciclos', views.month_cycles, name="month_cycles"),
    path('produtores/ciclos/<str:month_identifier>/', views.month_cycle_detail, name="month_cycle_detail"),
    path('produtores/ciclos/<str:month_identifier>/<int:week_cycle_number>/relatorio', views.week_cycle_report, name="week_cycle_report"),
    path('produtores/ciclos/<str:month_identifier>/<int:week_cycle_number>/pedidos', views.producer_cycle_requests, name="producer_cycle_requests"),
    path('produtores/pedido/<str:basket_number>', views.producer_payment_confirmation, name="producer_payment_confirmation"),
    path('produtores/produtos/', views.products_list_detail, name="products_list_detail"),
    path('pedido/<str:basket_number>', views.requested_basket_url, name="requested_basket_url"),
]
