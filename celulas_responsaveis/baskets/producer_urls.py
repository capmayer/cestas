from django.urls import path

from . import views

app_name = 'producer'
urlpatterns = [
    path('ciclos', views.producer_home, name="producer_home"),
    path('ciclos/<str:month_cycle_name>/', views.month_cycle_detail, name="month_cycle_detail"),
    path('ciclos/<str:month_cycle_name>/<int:week_cycle_number>', views.week_cycle_report, name="week_cycle_report"),
    path('novo_ciclo_semanal/', views.new_week_cycle, name="new_week_cycle"),
    path('novo_ciclo_mensal/', views.new_month_cycle, name="new_month_cycle"),
    path('produtos/', views.products_list_detail, name="products_list_detail"),
    path('', views.producer_home),
]
