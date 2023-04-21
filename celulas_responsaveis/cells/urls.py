from django.urls import path

from . import views

app_name = "cells"
urlpatterns = [
    path("", views.list_cells, name="list_cells"),
    path("nova", views.create_cell, name="create_cell"),
    path("concluido", views.application_complete, name="application_complete"),
    path("<str:cell_slug>", views.consumer_cell_detail, name="consumer_cell_detail"),
    path("<str:cell_slug>/coordenar", views.cell_management, name="management"),
    path("<str:cell_slug>/entrando/<str:role>", views.new_membership, name="new_membership"),
]
