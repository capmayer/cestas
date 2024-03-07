from django.urls import path

from . import views

app_name = "cells"
urlpatterns = [
    path("celulas/", views.list_cells, name="list_cells"),
    path("ccr/nova/", views.create_cell, name="create_cell"),
    path("ccr/concluido/", views.application_complete, name="application_complete"),
    path("ccr/<str:cell_slug>/", views.consumer_cell_detail, name="consumer_cell_detail"),
    path("g/<str:cell_slug>/", views.producer_cell_detail, name="producer_cell_detail"),
    path("g/<str:cell_slug>/entrar/", views.apply_to_producer_cell, name="apply_to_producer_cell"),
    path("g/<str:cell_slug>/entrando/<str:role>", views.new_producer_membership, name="new_producer_membership"),
    path("ccr/<str:cell_slug>/coordenar/", views.cell_management, name="management"),
    path("ccr/<str:cell_slug>/entrar/", views.apply_to_consumer_cell, name="apply_to_consumer_cell"),
    path("ccr/<str:cell_slug>/entrando/<str:role>", views.new_consumer_membership, name="new_consumer_membership"),
    path("produtores/configuracoes", views.producer_cell_settings, name="producer_settings"),
    path("plano/", views.consumer_participation_settings, name="consumer_participation_settings"),
    path("plano/cancelar/", views.consumer_stop_participation, name="consumer_stop_participation"),
    path("plano/cancelamento/", views.consumer_cancellation_survey, name="consumer_cancellation_survey"),

]
