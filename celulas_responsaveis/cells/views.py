from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
import folium

from celulas_responsaveis.cells.forms import CellRegistrationForm, ApplicationForm
from celulas_responsaveis.cells.models import Cell, CellLocation, Application, ApplicationAnswer, Membership, Role


def generate_cell_map(latitude: float, longitude: float) -> str:
    m = folium.Map(location=[latitude, longitude], zoom_start=25)
    folium.Marker(location=[latitude, longitude]).add_to(m)

    return m._repr_html_()


def cell_detail(request, cell_slug: str):
    cell = get_object_or_404(Cell, slug=cell_slug)
    cell_location = CellLocation.objects.get(cell=cell)

    is_member = False
    is_organizer = False

    if request.user.is_authenticated:
        # If user is a member we don't need to show application button.
        is_member = cell.members.filter(id=request.user.id).exists()

        organizer = Role.objects.get(name="Organização")
        is_organizer = cell.members.through.objects.filter(cell=cell, person=request.user, role=organizer).exists()

    context = {
        "is_member": is_member,
        "is_organizer": is_organizer,
        "cell": cell,
        "cell_map": generate_cell_map(cell_location.latitude, cell_location.longitude),
    }
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
    all_cells = Cell.objects.all()
    cells_location = CellLocation.objects.all()
    cells = zip(all_cells, cells_location)
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

    if request.method == "POST":
        application_form = ApplicationForm(request.POST)

        if application_form.is_valid():
            application = Application()
            application.cell = cell
            application.person = request.user

            application.save()

            if hasattr(application_form, "questions_instances"):

                for question in application_form.questions_instances:
                    answer = ApplicationAnswer()
                    answer.application = application
                    answer.question = question
                    answer.answer = application_form.cleaned_data[question.name]
                    answer.save()

            return redirect("cells:application_complete")

    else:
        application_form = ApplicationForm()

    context = {
        "cell": cell,
        "application_form": application_form,
    }

    return render(request, "cells/new_application.html", context)


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
    application = Application.objects.get(uuid=application_uuid)
    application.is_pending = False
    application.approved = True
    application.approved_by = request.user

    application.save()

    role = Role.objects.get(name="Consumidor")
    membership = {
        'role': role
    }

    cell = Cell.objects.get(slug=cell_slug)
    cell.members.add(application.person, through_defaults=membership)
    cell.save()

    # Send email to approved person with info.

    return redirect("cells:members", cell_slug=cell_slug)
