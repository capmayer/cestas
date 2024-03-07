from django.urls import path

from . import views

app_name = "wallets"
urlpatterns = [
    path("caderneta/", views.consumer_wallet, name="consumer_wallet"),
    path("depositar/", views.consumer_deposit, name="consumer_deposit"),
    path('deposito_redirect/<str:deposit_number>/', views.redirect_deposit_confirmation, name="redirect_deposit_confirmation"),
    path('deposito/<str:deposit_number>/', views.consumer_deposit_detail, name="consumer_deposit_detail"),
]
