from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
import folium
from django.urls import reverse
from django.utils.http import urlencode

from celulas_responsaveis.cells.forms import ConsumerCellRegistrationForm
from celulas_responsaveis.cells.models import ConsumerCell, CellLocation, Application, Role, ConsumerMembership


def generate_cell_map(latitude: float, longitude: float) -> str:
    m = folium.Map(location=[latitude, longitude], zoom_start=25)
    folium.Marker(location=[latitude, longitude]).add_to(m)

    return m._repr_html_()


def consumer_cell_detail(request, cell_slug: str):
    """
        Página da célula.

    Centraliza as ações que podem ser realizadas em relação à célula de consumidores.
    """

    cell = get_object_or_404(ConsumerCell, slug=cell_slug)
    location = CellLocation.objects.get(cell=cell)

    context = {
        "is_cell_member": False,
        "is_organizer": False,
        "cell": cell,
        "location": location,
    }

    if request.user.is_authenticated:
        # If user is a member we don't need to show application button.
        person_membership = ConsumerMembership.objects.filter(person=request.user)

        cell_member_membership = person_membership.filter(cell=cell)
        context["is_cell_member"] = cell_member_membership.exists()

        organizer = Role.objects.get(name="coordenacao")

        is_organizer = cell_member_membership.filter(role=organizer).exists()
        context["is_organizer"] = is_organizer

    return render(request, "cells/cell_detail.html", context)


@login_required
def create_cell(request):
    if request.method == "POST":
        form = ConsumerCellRegistrationForm(request.POST)

        if form.is_valid():
            cell = ConsumerCell()
            cell.name = form.cleaned_data["name"]
            cell.description = form.cleaned_data["description"]
            cell.save()

            cell_location = CellLocation()
            cell_location.cell = cell
            cell_location.address = form.cleaned_data["address"]
            cell_location.city = form.cleaned_data["city"]
            cell_location.state = form.cleaned_data["state"]
            cell_location.neighborhood = form.cleaned_data["neighborhood"]
            cell_location.save()

            # Call script to register in IDEC pages.

            return redirect("cells:new_membership", cell_slug=cell.slug, role="coordenacao")
    else:
        form = ConsumerCellRegistrationForm()

    return render(request, "cells/cell_form.html", {"form": form})


def list_cells(request):
    # This only works with cells and locations length are equal.
    cells = ConsumerCell.objects.all()
    locations = CellLocation.objects.all()

    cells_locations = list(zip(cells, locations))
    context = {
        "cells": cells_locations,
    }

    return render(request, "cells/all_cells.html", context=context)


def application_complete(request):
    return render(request, "cells/application_complete.html")

#
# @login_required
# def new_application(request, cell_slug: str):
#     cell = get_object_or_404(ConsumerCell, slug=cell_slug)
#
#     if request.user.is_authenticated:
#         is_member = cell.members.filter(id=request.user.id)
#         has_application = Application.objects.filter(person=request.user, cell=cell, is_pending=True)
#
#         if is_member.exists() or has_application.exists():
#             return HttpResponse("Você já é membro ou já possui uma aplicação para esta célula!")
#
#     application = Application()
#     application.cell = cell
#     application.person = request.user
#     application.save()
#
#     return redirect("cells:application_complete")

def apply_to_consumer_cell(request, cell_slug: str):
    """
        Define os caminhos para ingressar en uma célula.

    Pessoa acessou o link para entrar na célula ou chegou nela atráves de buscar na internet/plataforma.
    Caso ela esteja deslogada da plataforma, inferimos que ainda não possui cadastro. Caso esteja logada, verificamos
    se já é membra, se não encaminha para entrar na célula.
    """
    cell = get_object_or_404(ConsumerCell, slug=cell_slug)

    if request.user.is_authenticated:
        membership = ConsumerMembership.objects.filter(person=request.user.id).first()

        if membership:
            messages.warning(request, f"Você já faz parte da CCR {membership.cell}")
            return redirect("cells:consumer_cell_detail", cell_slug=cell_slug)

        else:
            return redirect("cells:new_membership", cell_slug=cell_slug, role="membro")

    else:
        cell_membership_url = urlencode({"next": reverse("cells:new_membership", kwargs={"cell_slug": cell_slug, "role": "membro"})})
        signup_url = reverse('account_signup')
        messages.warning(request, "É necessário criar uma conta ou entrar em uma conta existente para continuar.")
        return redirect(f"{signup_url}?{cell_membership_url}")


def new_membership(request, cell_slug: str, role: str = "membro"):
    """
        Cria a relação da pessoa com a célula.

     View com função de criar a relação entre pessoa e célula. É utilizado para adicionar membros em células de consumo.
     O paramêtro 'role' define a função do membro na célula, por exemplo, estar na coordenação da célula.
    """
    cell = get_object_or_404(ConsumerCell, slug=cell_slug)

    if request.user.is_authenticated:
        is_member = cell.members.filter(id=request.user.id)

        if is_member.exists():
            return redirect("baskets:request_products")

    role = Role.objects.get(name=role)

    membership_content = {
        "role": role,
        "is_active": True,
    }

    cell.members.add(request.user, through_defaults=membership_content)
    cell.save()

    if role.name == "membro":
        return redirect("baskets:request_products")
    else:
        return redirect("cells:consumer_cell_detail", cell_slug=cell_slug)

@login_required
def cell_management(request, cell_slug: str):
    cell = get_object_or_404(ConsumerCell, slug=cell_slug)
    membership = ConsumerMembership.objects.filter(cell=cell)
    applications = Application.objects.filter(cell=cell)

    context = {
        "applications": applications,
        "cell": cell,
        "membership": membership,
    }
    return render(request, "cells/cell_management.html", context)

# @login_required
# def approve_application(request, cell_slug: str, application_uuid: str):
#     """Not being used."""
#     application = get_object_or_404(Application, uuid=application_uuid)
#     cell = get_object_or_404(ConsumerCell, slug=cell_slug)
#     application.is_pending = False
#     application.approved = True
#     application.approved_by = request.user
#
#     application.save()
#
#     role = Role.objects.get(name="Consumidor")
#
#     membership_content = {
#         "role": role,
#         "is_active": True,
#     }
#
#     cell.members.add(application.person, through_defaults=membership_content)
#     cell.save()
#
#     return redirect("cells:members", cell_slug=cell_slug)
