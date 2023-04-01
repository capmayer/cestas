from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
import folium
from django.urls import reverse
from django.utils.http import urlencode

from celulas_responsaveis.cells.forms import CellRegistrationForm, ApplicationForm
from celulas_responsaveis.cells.models import Cell, CellLocation, Application, ApplicationAnswer, Membership, Role, \
    CellType


def generate_cell_map(latitude: float, longitude: float) -> str:
    m = folium.Map(location=[latitude, longitude], zoom_start=25)
    folium.Marker(location=[latitude, longitude]).add_to(m)

    return m._repr_html_()


def cell_detail(request, cell_slug: str):
    """
        Página da célula.

    Centraliza as ações que podem ser realizadas em relação à célula. Cada tipo de célula possue ações diferentes.
    """

    cell = get_object_or_404(Cell, slug=cell_slug)
    location = CellLocation.objects.get(cell=cell)

    context = {
        "is_cell_member": False,
        "is_organizer": False,
        "can_connect": False,
        "cell_already_connected": False,
        "cell": cell,
        "location": location,
    }

    if request.user.is_authenticated:
        # If user is a member we don't need to show application button.
        person_membership = Membership.objects.filter(person=request.user)

        cell_member_membership = person_membership.filter(cell=cell)
        context["is_cell_member"] = cell_member_membership.exists()

        organizer = Role.objects.get(name="coordenacao")

        is_organizer = cell_member_membership.filter(role=organizer).exists()
        context["is_organizer"] = is_organizer

        if cell.cell_type is CellType.PRODUCER.value:
            person_organize_cells = person_membership.filter(role=organizer, cell__cell_type=CellType.CONSUMER.value)

            person_cell = person_organize_cells.last()

            if person_cell and person_cell.cell.producer_cell == cell:
                context["cell_already_connected"] = True

            if cell.is_producer_cell and person_organize_cells.exists():
                context["can_connect"] = True



    return render(request, "cells/cell_detail.html", context)

def get_person_cell_by_role(request, role, cell_type):
    person_role = Role.objects.get(name=role)
    membership = Membership.objects.filter(person=request.user, role=person_role, cell__cell_type=cell_type)

    if membership:
        return membership.last().cell
    else:
        return None


@login_required
def connect_cells(request, cell_slug: str):
    producer_cell = get_object_or_404(Cell, slug=cell_slug)

    consumer_cell = get_person_cell_by_role(request, "coordenacao", CellType.CONSUMER.value)

    consumer_cell.producer_cell = producer_cell
    consumer_cell.save()

    return redirect("cells:cell_detail", cell_slug=cell_slug)


@login_required
def create_cell(request):
    if request.method == "POST":
        form = CellRegistrationForm(request.POST)

        if form.is_valid():
            cell = Cell()
            cell.name = form.cleaned_data["name"]
            cell.description = form.cleaned_data["description"]
            cell.cell_type = form.cleaned_data["cell_type"]
            cell.save()

            cell_location = CellLocation()
            cell_location.cell = cell
            cell_location.address = form.cleaned_data["address"]
            cell_location.city = form.cleaned_data["city"]
            cell_location.state = form.cleaned_data["state"]
            cell_location.save()

            # Call script to register in IDEC pages.

            return redirect("cells:new_membership", cell_slug=cell.slug, role="coordenacao")
    else:
        form = CellRegistrationForm()

    return render(request, "cells/cell_form.html", {"form": form})


def list_cells(request):
    # This only works with cells and locations lenght are equal.
    cells = Cell.objects.filter(cell_type=CellType.CONSUMER.value)
    locations = CellLocation.objects.filter(cell__cell_type=CellType.CONSUMER.value)

    producer_cells = Cell.objects.filter(cell_type=CellType.PRODUCER.value)
    cells_locations = list(zip(cells, locations))
    context = {
        "cells": cells_locations,
        "producer_cells": producer_cells,
    }

    return render(request, "cells/all_cells.html", context=context)


def application_complete(request):
    return render(request, "cells/application_complete.html")


@login_required
def new_application(request, cell_slug: str):
    cell = get_object_or_404(Cell, slug=cell_slug)

    if request.user.is_authenticated:
        is_member = cell.members.filter(id=request.user.id)
        has_application = Application.objects.filter(person=request.user, cell=cell, is_pending=True)

        if is_member.exists() or has_application.exists():
            return HttpResponse("Você já é membro ou já possui uma aplicação para esta célula!")

    application = Application()
    application.cell = cell
    application.person = request.user
    application.save()

    return redirect("cells:application_complete")

def cell_apply(request, cell_slug: str):
    """
        Define os caminhos para ingressar en uma célula.

    Pessoa acessou o link para entrar na célula ou chegou nela atráves de buscar na internet/plataforma.
    Caso ela esteja deslogada da plataforma, inferimos que ainda não possui cadastro. Caso esteja logada, verificamos
    se já é membra, se não encaminha para entrar na célula.
    """
    cell = get_object_or_404(Cell, slug=cell_slug)

    if request.user.is_authenticated:
        is_member = cell.members.filter(id=request.user.id)

        if is_member.exists():
            return HttpResponse("Já é membro.")

        else:
            return redirect("cells:new_membership", cell_slug=cell_slug, role="membro")

    else:
        cell_membership_url = urlencode({"next": reverse("cells:new_membership", kwargs={"cell_slug": cell_slug, "role": "membro"})})
        signup_url = reverse('account_signup')
        return redirect(f"{signup_url}?{cell_membership_url}")

@login_required
def new_membership(request, cell_slug: str, role: str = "membro"):
    """
        Cria a relação da pessoa com a célula/grupo.

     View com função de criar a relação entre pessoa e célula/grupo. É utilizado para adicionar membros em células de
     produção e consumo. O paramêtro 'role' define a função do membro na célula, por exemplo, estar na coordenação da
     célula/grupo.


    """
    cell = get_object_or_404(Cell, slug=cell_slug)

    if request.user.is_authenticated:
        is_member = cell.members.filter(id=request.user.id)

        if is_member.exists():
            if cell.cell_type is CellType.PRODUCER.value:
                return redirect("producer:home_producer")
            elif cell.cell_type is CellType.CONSUMER.value:
                return redirect("baskets:additional_products_list", cell_slug=cell_slug)

    role = Role.objects.get(name=role)

    membership_content = {
        "role": role,
        "is_active": True,
    }

    cell.members.add(request.user, through_defaults=membership_content)
    cell.save()

    if role.name == "membro":
        if cell.cell_type is CellType.PRODUCER.value:
            return redirect("producer:home_producer")
        elif cell.cell_type is CellType.CONSUMER.value:
            return redirect("baskets:additional_products_list", cell_slug=cell_slug)
    else:
        return redirect("cells:cell_detail", cell_slug=cell_slug)

def cell_managment(request, cell_slug: str):
    cell = get_object_or_404(Cell, slug=cell_slug)
    membership = Membership.objects.filter(cell=cell)
    applications = Application.objects.filter(cell=cell)

    context = {
        "applications": applications,
        "cell": cell,
        "membership": membership,
    }
    return render(request, "cells/cell_managment.html", context)


def approve_application(request, cell_slug: str, application_uuid: str):
    """Not being used."""
    application = get_object_or_404(Application, uuid=application_uuid)
    cell = get_object_or_404(Cell, slug=cell_slug)
    application.is_pending = False
    application.approved = True
    application.approved_by = request.user

    application.save()

    role = Role.objects.get(name="Consumidor")

    membership_content = {
        "role": role,
        "is_active": True,
    }

    cell.members.add(application.person, through_defaults=membership_content)
    cell.save()

    return redirect("cells:members", cell_slug=cell_slug)
