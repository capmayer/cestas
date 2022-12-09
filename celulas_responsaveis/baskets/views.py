import datetime

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from celulas_responsaveis.baskets.forms import AdditionalProductsListFormSet, BasketFormSet
from celulas_responsaveis.baskets.models import AdditionalBasket, AdditionalProductsList, Cycle, SoldProduct
from celulas_responsaveis.cells.models import Cell, Role, Membership


def home(request):
    if not request.user.is_authenticated:
        return redirect("account_login")

    producer = Role.objects.get(name="Produtor")
    is_producer = Membership.objects.filter(person=request.user, role=producer).exists()

    if is_producer:
        return redirect('baskets:home_producer')

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

def home_producer(request):
    producer = Role.objects.get(name="Produtor")
    membership = Membership.objects.filter(person=request.user, role=producer)

    if not membership.exists():
        return redirect("account_login")

    cells = []

    for member in membership.all():
        cell_to_actions = {
            "name": member.cell.name,
            "report_url": reverse("baskets:cell_cycles", kwargs={"cell_slug": member.cell.slug})
        }
        cells.append(cell_to_actions)

    context = {
        "cells": cells,
    }

    return render(request, "baskets/home_producer.html", context=context)


def additional_products_detail(request, cell_slug: str, cycle_number: int):
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


def cycle_detail(request):
    pass


def cycle_report_detail(request, cell_slug: str, cycle_number: int):
    cell = Cell.objects.get(slug=cell_slug)
    cycle = Cycle.objects.get(cell=cell, number=cycle_number)
    baskets = []

    total_cycle_value = 0

    for basket in cycle.baskets.all():
        total_value = 0

        for product in basket.products.all():
            total_value += product.price * product.requested_quantity

        basket_dict = {
            "total_value": total_value,
            "obj": basket,
        }

        total_cycle_value += total_value
        baskets.append(basket_dict)

    context = {
        "cycle": cycle,
        "baskets": baskets,
        "total_cycle_value": total_cycle_value,
    }

    return render(request, "baskets/report_detail.html", context=context)


def cell_cycles(request, cell_slug: str):
    producer = Role.objects.get(name="Produtor")
    cell = Cell.objects.get(slug=cell_slug)
    is_producer = Membership.objects.filter(cell=cell, role=producer, person=request.user).exists()

    if not is_producer:
        return redirect("account_login")

    cycles = Cycle.objects.filter(cell=cell)

    context = {
        "cycles": cycles,
    }

    return render(request, "baskets/cell_cycles.html", context=context)


def additional_basket_detail(request, basket_uuid: str):
    return HttpResponse("Here you'll see your basket details")


def additional_products_list(request, cell_slug: str):
    cell = Cell.objects.get(slug=cell_slug)
    context = {}
    active_cycle = get_active_cycles(cell)

    if not active_cycle:
        return HttpResponse("Célula não possui um ciclo ativo.")

    cycle = active_cycle[0]

    is_cycle_over = check_requests_end(cycle)
    context["is_cycle_over"] = is_cycle_over

    products_list = AdditionalProductsList.objects.get(cycle=cycle)
    initial_values = []

    for product in products_list.products.all():
        initial_values.append({
            "name": product.name,
            "price": product.price,
            "unit": product.unit,
            "requested_quantity": 0,
        })

    if request.method == "POST":
        if is_cycle_over:
            return HttpResponse("Oops, os pedidos estão encerrados.")

        basket_formset = BasketFormSet(request.POST, initial=initial_values)

        additional_basket = AdditionalBasket()
        additional_basket.person = request.user
        additional_basket.cycle = cycle
        additional_basket.save()

        if basket_formset.is_valid():
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
                        sold_product.save()

            return redirect("baskets:basket_requested")

    basket_formset = BasketFormSet(initial=initial_values)

    context["cycle"] = cycle
    context["cell"] = cell
    context["basket_form"] = basket_formset

    return render(request, "baskets/additional_products_list.html", context=context)


def basket_requested(request):
    return render(request, "baskets/basket_requested.html")
