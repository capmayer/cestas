from django.urls import path

from . import views

app_name = 'baskets'
urlpatterns = [
    path('', views.home, name='home'),
    path('produtor/', views.home_producer, name="home_producer"),
    path('pedido_realizado', views.basket_requested, name="basket_requested"),
    path('<str:cell_slug>/adicionais/', views.additional_products_list, name="additional_products_list"),
    path('<str:cell_slug>/adicionais/<int:cycle_number>/', views.additional_products_detail, name="additional_products_detail"),
    # path('p/produtos/', views.products_list, name="products_list"),
    path('<str:cell_slug>/ciclos/', views.cell_cycles, name="cell_cycles"),
    path('<str:cell_slug>/ciclos/<int:cycle_number>/', views.cycle_report_detail, name="cycle_report_detail"),
]
