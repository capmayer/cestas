from django.urls import path

from . import views

app_name = 'producer'
urlpatterns = [
    path('', views.home_producer, name="home_producer"),
    path('<str:cell_slug>/novo_ciclo/', views.new_cycle, name="new_cycle"),
    path('<str:cell_slug>/ciclos/', views.cell_cycles, name="cell_cycles"),
    path('<str:cell_slug>/ciclos/<int:cycle_number>/relatorio', views.cycle_report_detail, name="cycle_report_detail"),
    path('<str:cell_slug>/adicionais/<int:cycle_number>/', views.additional_products_detail,
         name="additional_products_detail"),
]
