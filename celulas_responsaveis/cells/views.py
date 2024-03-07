from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect
import folium
from django.urls import reverse
from django.utils.http import urlencode

from celulas_responsaveis.baskets.forms import ConsumerBTChoiceForm
from celulas_responsaveis.baskets.models import ConsumerBasketTypeChoice
from celulas_responsaveis.baskets.views import get_producer_membership, get_consumer_membership
from celulas_responsaveis.cells.forms import ConsumerCellRegistrationForm, ProducerCellSettingsForm, \
    ConsumerMembershipForm
from celulas_responsaveis.cells.models import ConsumerCell, CellLocation, Application, Role, ConsumerMembership, \
    ProducerCell, ProducerMembership, ProducerCellSettings


def generate_cell_map(latitude: float, longitude: float) -> str:
    m = folium.Map(location=[latitude, longitude], zoom_start=25)
    folium.Marker(location=[latitude, longitude]).add_to(m)

    return m._repr_html_()

def producer_cell_detail(request, cell_slug: str):
    cell = get_object_or_404(ProducerCell, slug=cell_slug)

    context = {
        "cell": cell,
    }

    return render(request, "cells/producer_cell_detail.html", context=context)

def new_producer_membership(request, cell_slug: str, role: str = "membro"):
    """
        Cria a relação de membro do grupo.
    """
    cell = get_object_or_404(ProducerCell, slug=cell_slug)

    if request.user.is_authenticated:
        is_member = cell.members.filter(id=request.user.id)

        if is_member.exists():
            return redirect("producer:producer_home")

    role = Role.objects.get(name=role)

    membership_content = {
        "role": role,
        "is_active": True,
    }

    cell.members.add(request.user, through_defaults=membership_content)
    cell.save()

    return redirect("producer:producer_home")

def apply_to_producer_cell(request, cell_slug: str):
    """
        Produtora entrando ao grupo que faz parte.
    """
    cell = get_object_or_404(ProducerCell, slug=cell_slug)

    if request.user.is_authenticated:
        membership = ProducerMembership.objects.filter(person=request.user.id).first()

        if membership:
            messages.warning(request, f"Você já faz parte do {membership.cell}")
            return redirect("cells:producer_cell_detail", cell_slug=cell_slug)

        else:
            return redirect("cells:new_producer_membership", cell_slug=cell_slug, role="membro")

    else:
        cell_membership_url = urlencode({"next": reverse("cells:new_producer_membership", kwargs={"cell_slug": cell_slug, "role": "membro"})})
        signup_url = reverse('account_signup')
        messages.warning(request, "É necessário criar uma conta ou entrar em uma conta existente para continuar.")
        return redirect(f"{signup_url}?{cell_membership_url}")


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

    return render(request, "cells/consumer_cell_detail.html", context)


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

            return redirect("cells:new_consumer_membership", cell_slug=cell.slug, role="coordenacao")
    else:
        form = ConsumerCellRegistrationForm()

    return render(request, "cells/cell_form.html", {"form": form})


def list_cells(request):
    # This only works with cells and locations length are equal.
    cells_locations = CellLocation.objects.all().select_related('cell')
    context = {
        "cells_locations": cells_locations,
    }

    return render(request, "cells/all_cells.html", context=context)


def application_complete(request):
    return render(request, "cells/application_complete.html")

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
            return redirect("cells:new_consumer_membership", cell_slug=cell_slug, role="membro")

    else:
        cell_membership_url = urlencode({"next": reverse("cells:new_consumer_membership", kwargs={"cell_slug": cell_slug, "role": "membro"})})
        signup_url = reverse('account_signup')
        messages.warning(request, "É necessário criar uma conta ou entrar em uma conta existente para continuar.")
        return redirect(f"{signup_url}?{cell_membership_url}")


def new_consumer_membership(request, cell_slug: str, role: str = "membro"):
    """
        Cria a relação da pessoa com a célula.

     View com função de criar a relação entre pessoa e célula. É utilizado para adicionar membros em células de consumo.
     O paramêtro 'role' define a função do membro na célula, por exemplo, estar na coordenação da célula.
    """
    from celulas_responsaveis.wallets.models import Wallet

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

    if cell.producer_cell:
        membership = ConsumerMembership.objects.get(cell=cell, person=request.user)

        wallet = Wallet()
        wallet.consumer_membership = membership
        wallet.person = request.user
        wallet.producer_cell = membership.cell.producer_cell

        wallet.save()

    return redirect("cells:consumer_participation_settings")

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


@login_required
def producer_cell_settings(request):
    producer_membership = get_producer_membership(request.user)
    cell = producer_membership.cell
    cell_settings = ProducerCellSettings.objects.get(cell=cell)

    if request.method == "POST":
        cell_settings_form = ProducerCellSettingsForm(request.POST, instance=cell_settings)

        if cell_settings_form.is_valid():
            cell_settings_form.save()
            messages.success(request, "Alterações salvas.")
    else:
        cell_settings_form = ProducerCellSettingsForm(instance=cell_settings)

    context = {
        "cell": cell,
        "cell_settings_form": cell_settings_form,
    }

    return render(request, "cells/producer_cell_settings.html", context)


@login_required
def consumer_stop_participation(request):
    membership = get_consumer_membership(request.user)

    if request.method == "POST":
        cm_form = ConsumerMembershipForm(request.POST, instance=membership)

        if cm_form.is_valid():
            membership = cm_form.save(commit=False)
            membership.is_active = False
            membership.save()
            messages.success(request, "Sua participação foi cancelada.")

            return redirect("cells:consumer_cancellation_survey")

@login_required
def consumer_cancellation_survey(request):
    # TODO: add survey.
    membership = get_consumer_membership(request.user)
    context = {
        "membership": membership,
    }
    return render(request, "cells/consumer_cancellation_survey.html", context=context)

@login_required
def consumer_participation_settings(request):
    memberships = ConsumerMembership.objects.filter(person=request.user)

    if not memberships.exists():
        raise PermissionDenied("Você precisa fazer parte de alguma CCR para realizar essa ação.")

    membership = memberships.first()
    cell = membership.cell
    bt_choice = ConsumerBasketTypeChoice.objects.filter(person=request.user, consumer_cell=cell)

    if bt_choice.exists():
        bt_choice = bt_choice.first()
    else:
        bt_choice = None


    if request.method == "POST":
        bt_choice_form = ConsumerBTChoiceForm(request.POST, instance=bt_choice, producer_cell=cell.producer_cell)
        if bt_choice_form.is_valid():
            bt_choice = bt_choice_form.save(commit=False)
            bt_choice.consumer_cell = cell
            bt_choice.person = request.user
            bt_choice.save()

            messages.success(request, message="Alterações salvas.")
            return redirect("baskets:consumer_home")
    else:
        bt_choice_form = ConsumerBTChoiceForm(instance=bt_choice, producer_cell=cell.producer_cell)

    context = {
        "cell": cell,
        "bt_choice_form": bt_choice_form,
    }
    return render(request, "cells/consumer_participation_settings.html", context=context)



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
