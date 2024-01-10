from django.urls import path

from . import views

app_name = 'producer'
urlpatterns = [
    path('produtores/', views.producer_home, name="producer_home"),
    path('produtores/nova-semana/', views.new_week_cycle, name="new_week_cycle"),
    path('produtores/ciclos', views.month_cycles, name="month_cycles"),
    path('produtores/ciclos/<str:month_identifier>/', views.month_cycle_detail, name="month_cycle_detail"),
    path('produtores/ciclos/<str:month_identifier>/<int:week_cycle_number>/relatorio', views.week_cycle_report, name="week_cycle_report"),
    path('produtores/ciclos/<str:month_identifier>/<int:week_cycle_number>/pedidos', views.producer_cycle_requests, name="producer_cycle_requests"),
    path('produtores/ciclos/<str:month_identifier>/<int:week_cycle_number>/produtos', views.week_cycle_total_products, name="week_cycle_total_products"),
    path('produtores/deposito/<str:deposit_number>', views.producer_deposit_confirmation, name="producer_deposit_confirmation"),
    path('produtores/produtos/', views.products_list_detail, name="products_list_detail"),
    path('produtores/produtos/novo', views.producer_new_product, name="new_product"),
    path('produtores/produtos/<int:product_id>', views.producer_product_detail, name="product_detail"),
    path('produtores/produtos/<int:product_id>/delete', views.producer_product_delete, name="product_delete"),
    path('produtores/celulas/', views.producer_cells_list, name="producer_cells_list"),
    path('produtores/cadernetas/', views.consumers_wallets, name="consumers_wallets"),
    path('produtores/cadernetas/<str:consumer_username>/', views.consumer_wallet, name="consumer_wallet"),
    path('produtores/depositos/', views.consumers_deposits, name="consumers_deposits"),
]
