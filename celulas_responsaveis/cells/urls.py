from django.urls import path

from . import views

app_name = "cells"
urlpatterns = [
    path("", views.list_cells, name="list_cells"),
    path("nova", views.create_cell, name="create_cell"),
    path("concluido", views.application_complete, name="application_complete"),
    path("<str:cell_slug>", views.cell_detail, name="cell_detail"),
    path("<str:cell_slug>/coordenar", views.cell_managment, name="managment"),
    path("<str:cell_slug>/membros/aplicacao/<str:application_uuid>", views.approve_application, name="approve_application"),
    path("<str:cell_slug>/aplicar", views.new_application, name="new_application"),
    path("<str:cell_slug>/entrar", views.cell_apply, name="cell_apply"),
    path("<str:cell_slug>/entrando/<str:role>", views.new_membership, name="new_membership"),
    path("<str:cell_slug>/conectando_com_celula", views.connect_cells, name="connect_cells"),
]
