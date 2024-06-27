from django.urls import path

from . import views

app_name = 'producer'
urlpatterns = [
    path('produtores/', views.producer_home, name="producer_home"),
    path('produtores/nova-semana/', views.new_week_cycle, name="new_week_cycle"),
    path('produtores/novo-mes/', views.new_month_cycle, name="new_month_cycle"),
    path('produtores/cesta-da-semana/', views.new_week_basket, name="new_week_basket"),
    path('produtores/ciclos', views.month_cycles, name="month_cycles"),
    path('produtores/ciclos/iniciar/', views.start_month_cycle, name="start_month_cycle"),
    path('produtores/ciclos/<str:month_identifier>/', views.month_cycle_detail, name="month_cycle_detail"),
    path('produtores/ciclos/<str:month_identifier>/<int:week_cycle_number>/', views.producer_week_cycle_detail,
         name="week_cycle_detail"),
    path('produtores/ciclos/<str:month_identifier>/<int:week_cycle_number>/editar/', views.producer_edit_week_cycle,
         name="edit_week_cycle"),
    path('produtores/ciclos/<str:month_identifier>/<int:week_cycle_number>/relatorio/', views.week_cycle_report, name="week_cycle_report"),
    path('produtores/ciclos/<str:month_identifier>/<int:week_cycle_number>/cestas/', views.week_cycle_baskets, name="week_cycle_baskets"),
    path('produtores/ciclos/<str:month_identifier>/<int:week_cycle_number>/pedidos', views.producer_cycle_requests, name="producer_cycle_requests"),
    path('produtores/ciclos/<str:month_identifier>/<int:week_cycle_number>/produtos', views.week_cycle_total_products, name="week_cycle_total_products"),
    path('produtores/deposito/<str:deposit_number>', views.producer_deposit_confirmation, name="producer_deposit_confirmation"),
    path('produtores/deposito/<str:deposit_number>/rejeitar', views.producer_deposit_reject, name="producer_deposit_reject"),
    path('produtores/produtos/', views.products_list_detail, name="products_list_detail"),
    path('produtores/produtos/novo', views.producer_new_product, name="new_product"),
    path('produtores/produtos/<int:product_id>', views.producer_product_detail, name="product_detail"),
    path('produtores/produtos/<int:product_id>/delete', views.producer_product_delete, name="product_delete"),
    path('produtores/celulas/', views.producer_cells_list, name="producer_cells_list"),
    path('produtores/consumidores/', views.consumers_list, name="consumers_list"),
    path('produtores/consumidores/<str:consumer_username>/', views.consumer_detail, name="consumer_detail"),
    path('produtores/caderneta/<str:consumer_username>/', views.consumer_wallet, name="consumer_wallet"),
    path('produtores/depositos/', views.consumers_deposits, name="consumers_deposits"),
]
