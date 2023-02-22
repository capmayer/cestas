import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from celulas_responsaveis.baskets.forms import AdditionalProductsListFormSet, BasketFormSet, CycleForm
from celulas_responsaveis.baskets.models import AdditionalBasket, AdditionalProductsList, Cycle, SoldProduct
from celulas_responsaveis.cells.models import Cell, Role, Membership, PaymentInfo


def home(request):
    if not request.user.is_authenticated:
        return redirect("account_login")

    producer = Role.objects.get(name="Produtor")
    is_producer = Membership.objects.filter(person=request.user, role=producer).exists()

    if is_producer:
        return redirect('producer:home_producer')

    baskets = AdditionalBasket.objects.filter(person=request.user)

    context = {
        "baskets": baskets,
    }
    return render(request, "baskets/home.html", context=context)


def get_active_cycles(cell: Cell):
    today = datetime.date.today()
    last_week = today + datetime.timedelta(-7)
    return Cycle.objects.filter(cell=cell, begin__range=[last_week, today])

def check_requests_end(cycle: Cycle) -> bool:
    today = datetime.date.today()
    return today > cycle.requests_end

@login_required
def home_producer(request):
    producer = Role.objects.get(name="Produtor")
    membership = Membership.objects.filter(person=request.user, role=producer)

    if not membership.exists():
        return redirect("account_login")

    cells = []

    for member in membership.all():
        cell_to_actions = {
            "name": member.cell.name,
            "report_url": reverse("producer:cell_cycles", kwargs={"cell_slug": member.cell.slug})
        }
        cells.append(cell_to_actions)

    context = {
        "cells": cells,
    }

    return render(request, "baskets/home_producer.html", context=context)

@login_required
def additional_products_detail(request, cell_slug: str, cycle_number: int):
    """Used by productor"""
    cell = Cell.objects.get(slug=cell_slug)
    products_list = AdditionalProductsList.objects.get(cycle__number=cycle_number, cycle__cell=cell)

    context = dict()
    context["products_list"] = products_list

    if request.method == "POST":
        additional_products_list_form = AdditionalProductsListFormSet(request.POST, instance=products_list)
        context["additional_products_list_form"] = additional_products_list_form
        if additional_products_list_form.is_valid():
            additional_products_list_form.save()
            context["message"] = "Lista salva."
            return render(request, "baskets/additional_products_detail.html", context=context)
        else:
            return render(request, "baskets/additional_products_detail.html", context=context)

    additional_products_list_form = AdditionalProductsListFormSet(instance=products_list)

    context["additional_products_list_form"] = additional_products_list_form

    return render(request, "baskets/additional_products_detail.html", context=context)

@login_required
def new_cycle(request, cell_slug: str):
    """Used by producer to create new cycles."""
    cell = Cell.objects.get(slug=cell_slug)
    last_cycle = Cycle.objects.filter(cell=cell).latest("number")

    context = {
        "cell": cell,
        "last_cycle": last_cycle,
    }

    if request.method == "POST":
        cycle_form = CycleForm(request.POST)

        if cycle_form.is_valid():
            cycle = Cycle()
            cycle.number = cycle_form.cleaned_data["number"]
            cycle.begin = cycle_form.cleaned_data["begin"]
            cycle.requests_end = cycle_form.cleaned_data["requests_end"]
            cycle.end = cycle_form.cleaned_data["end"]
            cycle.cell = cell

            cycle.save()

            if last_cycle:
                additional_products_list = AdditionalProductsList.objects.get(cycle=last_cycle)
                products = [product for product in additional_products_list.products.all()]
                additional_products_list.pk = None
                additional_products_list.cycle = cycle
                additional_products_list.save()

                for product in products:
                    product.additional_products_list = additional_products_list
                    product.pk = None
                    product.save()

                return HttpResponse("Hey")

            else:
                return HttpResponse("Config products now")
    else:
        cycle_number = last_cycle.number + 1 if last_cycle else 1
        cycle_form = CycleForm(initial={"number": cycle_number})
        context["cycle_form"] = cycle_form

    return render(request, "baskets/new_cycle.html", context)

@login_required
def cycle_report_detail(request, cell_slug: str, cycle_number: int):
    """Used by productor."""
    cell = Cell.objects.get(slug=cell_slug)
    cycle = Cycle.objects.get(cell=cell, number=cycle_number)

    total_cycle_value = 0

    for basket in cycle.baskets.all():
        total_cycle_value += basket.total_price

    context = {
        "cycle": cycle,
        "total_cycle_value": total_cycle_value,
    }

    return render(request, "baskets/report_detail.html", context=context)


@login_required
def cell_cycles(request, cell_slug: str):
    """Used by productor."""
    producer = Role.objects.get(name="Produtor")
    cell = Cell.objects.get(slug=cell_slug)
    is_producer = Membership.objects.filter(cell=cell, role=producer, person=request.user).exists()

    if not is_producer:
        return redirect("account_login")

    cycles = Cycle.objects.filter(cell=cell).order_by("-number")

    context = {
        "cycles": cycles,
        "cell": cell,
    }

    return render(request, "baskets/cell_cycles.html", context=context)


def additional_basket_detail(request, basket_uuid: str):
    return HttpResponse("Here you'll see your basket details")


@login_required
def additional_products_list(request, cell_slug: str):
    """Used by consumer."""
    cell = Cell.objects.get(slug=cell_slug)
    context = {}
    cycle = Cycle.objects.filter(cell=cell).latest("number")

    if not cycle:
        return HttpResponse("Célula não possui um ciclo ativo.")

    has_basket = AdditionalBasket.objects.filter(cycle=cycle, person=request.user).exists()
    if has_basket:
        return HttpResponse("Pedido de adicionais já realizado para este ciclo.")

    is_cycle_over = check_requests_end(cycle)
    context["is_cycle_over"] = is_cycle_over

    products_list = AdditionalProductsList.objects.get(cycle=cycle)

    if not products_list:
        return HttpResponse("A lista de pedidos adicionais ainda não foi disponibilizada.")

    initial_values = []

    for product in products_list.products.filter(is_available=True):
        initial_values.append({
            "name": product.name,
            "price": product.price,
            "unit": product.unit,
            "requested_quantity": 0,
        })

    if request.method == "POST":
        if is_cycle_over:
            return HttpResponse("Oops, os pedidos estão encerrados para esse ciclo.")

        basket_formset = BasketFormSet(request.POST, initial=initial_values)

        if basket_formset.is_valid():
            additional_basket = AdditionalBasket()
            additional_basket.person = request.user
            additional_basket.cycle = cycle
            additional_basket.save()

            total_price = 0.0

            for form in basket_formset:
                if form.is_valid():
                    requested_quantity = form.cleaned_data["requested_quantity"]

                    if requested_quantity > 0.0:
                        sold_product = SoldProduct()
                        sold_product.name = form.cleaned_data["name"]
                        sold_product.unit = form.cleaned_data["unit"]
                        sold_product.price = form.cleaned_data["price"]
                        sold_product.requested_quantity = requested_quantity
                        sold_product.basket = additional_basket
                        total_price += sold_product.price * sold_product.requested_quantity
                        sold_product.save()

            additional_basket.total_price = total_price
            additional_basket.save()

            return redirect("baskets:basket_requested", cell_slug=cell_slug, request_uuid=additional_basket.uuid)

    basket_formset = BasketFormSet(initial=initial_values)

    context["cycle"] = cycle
    context["cell"] = cell
    context["basket_form"] = basket_formset

    return render(request, "baskets/additional_products_list.html", context=context)


@login_required
def basket_requested(request, cell_slug: str, request_uuid: str):
    cell = get_object_or_404(Cell, slug=cell_slug)
    payment_info = PaymentInfo.objects.get(cell=cell)
    additional_basket_requested = AdditionalBasket.objects.get(uuid=request_uuid)

    context = {
        "payment_info": payment_info,
        "cell": cell,
        "total_price": additional_basket_requested.total_price,
    }
    return render(request, "baskets/basket_requested.html", context)
