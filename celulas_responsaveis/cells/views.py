from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
import folium
from django.urls import reverse
from django.utils.http import urlencode

from celulas_responsaveis.cells.forms import CellRegistrationForm, ApplicationForm
from celulas_responsaveis.cells.models import Cell, CellLocation, Application, ApplicationAnswer, Membership, Role


def generate_cell_map(latitude: float, longitude: float) -> str:
    m = folium.Map(location=[latitude, longitude], zoom_start=25)
    folium.Marker(location=[latitude, longitude]).add_to(m)

    return m._repr_html_()


def cell_detail(request, cell_slug: str):
    cell = get_object_or_404(Cell, slug=cell_slug)

    is_member = False
    is_organizer = False

    context = {
        "is_member": is_member,
        "is_organizer": is_organizer,
        "cell": cell,
    }

    if request.user.is_authenticated:
        # If user is a member we don't need to show application button.
        context["is_member"] = cell.members.filter(id=request.user.id).exists()

        organizer = Role.objects.get(name="Organização")
        context["is_organizer"] = cell.members.through.objects.filter(cell=cell, person=request.user, role=organizer).exists()


    return render(request, "cells/cell_detail.html", context)


def create_cell(request):
    if request.method == "POST":
        form = CellRegistrationForm(request.POST)

        if form.is_valid():
            cell = Cell()
            cell.name = form.cleaned_data["name"]
            cell.description = form.cleaned_data["description"]
            cell.save()

            cell_location = CellLocation()
            cell_location.cell = cell
            cell_location.address = form.cleaned_data["address"]
            cell_location.city = form.cleaned_data["city"]
            cell_location.state = form.cleaned_data["state"]
            cell_location.latitude = form.cleaned_data["latitude"]
            cell_location.longitude = form.cleaned_data["longitude"]
            cell_location.save()

            # Call script to register in IDEC pages.

            return HttpResponse("Done")
    else:
        form = CellRegistrationForm()

    return render(request, "cells/cell_form.html", {"form": form})


def list_cells(request):
    cells = Cell.objects.all()
    return render(request, "cells/all_cells.html", {"cells": cells})


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

def consumer_apply(request, cell_slug: str):
    cell = get_object_or_404(Cell, slug=cell_slug)

    if request.user.is_authenticated:
        is_member = cell.members.filter(id=request.user.id)

        if is_member.exists():
            return redirect("baskets:additional_products_list", cell_slug=cell_slug)

        else:
            return redirect("cells:new_membership", cell_slug=cell_slug)

    else:
        cell_membership_url = urlencode({'next': reverse('cells:new_membership', kwargs={'cell_slug': cell_slug})})
        signup_url = reverse('account_signup')
        return redirect(f"{signup_url}?{cell_membership_url}")

@login_required
def new_membership(request, cell_slug: str):
    cell = get_object_or_404(Cell, slug=cell_slug)

    if request.user.is_authenticated:
        is_member = cell.members.filter(id=request.user.id)

        if is_member.exists():
            return redirect("baskets:additional_products_list", cell_slug=cell_slug)

    role = Role.objects.get(name="Consumidor")

    membership_content = {
        "role": role,
        "is_active": True,
    }

    cell.members.add(request.user, through_defaults=membership_content)
    cell.save()

    return redirect("baskets:additional_products_list", cell_slug=cell_slug)

def members(request, cell_slug: str):
    cell = get_object_or_404(Cell, slug=cell_slug)
    membership = Membership.objects.filter(cell=cell)
    applications = Application.objects.filter(cell=cell)

    context = {
        "applications": applications,
        "cell": cell,
        "membership": membership,
    }
    return render(request, "cells/members.html", context)


def approve_application(request, cell_slug: str, application_uuid: str):
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
