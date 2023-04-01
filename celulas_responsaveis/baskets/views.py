import datetime

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse

from celulas_responsaveis.baskets.forms import ProductsListFormSet, BasketFormSet, CycleForm
from celulas_responsaveis.baskets.models import AdditionalBasket, AdditionalProductsList, Cycle, SoldProduct, Unit
from celulas_responsaveis.cells.models import Cell, Role, Membership, PaymentInfo, CellType


@login_required
def home(request):
    baskets = AdditionalBasket.objects.filter(person=request.user)

    context = {
        "baskets": baskets,
    }
    return render(request, "baskets/home.html", context=context)


def get_active_cycles(cell: Cell):
    today = datetime.date.today()
    last_week = today + datetime.timedelta(-7)
    return Cycle.objects.filter(cell=cell, begin__range=[last_week, today])

def is_cycle_over(cycle: Cycle) -> bool:
    today = datetime.date.today()
    return today > cycle.requests_end

@login_required
def home_producer(request):
    """
        Paǵina principal do/a produtora.

    Página que apresenta as células atendendidas pelo grupo de produção para o/a produtora.
    """
    memberships = Membership.objects.filter(person=request.user, cell__cell_type=CellType.PRODUCER.value)

    if not memberships:
        return redirect("cells:list_cells")

    cells = dict()

    for membership in memberships:
        consumer_cells = membership.cell.consumer_cells.all()
        cells[membership.cell] = consumer_cells

    context = {
        "cells": cells.items(),
    }

    return render(request, "baskets/home_producer.html", context=context)

@login_required
def additional_products_detail(request, cell_slug: str, cycle_number: int):
    """Used by productor"""
    cell = Cell.objects.get(slug=cell_slug)
    cycle = Cycle.objects.get(consumer_cell=cell, number=cycle_number)
    products_lists = AdditionalProductsList.objects.filter(cycle=cycle)
    products_list = products_lists[0] if products_lists else None
    context = dict()
    context["products_list"] = products_list

    if request.method == "POST":
        if not products_list:
            products_list = AdditionalProductsList()
            products_list.cycle = cycle
            products_list.save()

        additional_products_list_form = ProductsListFormSet(request.POST, instance=products_list)

        if additional_products_list_form.is_valid():
            additional_products_list_form.save()
            context["additional_products_list_form"] = additional_products_list_form
            context["message"] = "Lista salva."
            return render(request, "baskets/additional_products_detail.html", context=context)
        else:
            return render(request, "baskets/additional_products_detail.html", context=context)

    additional_products_list_form = ProductsListFormSet(instance=products_list)

    context["additional_products_list_form"] = additional_products_list_form

    return render(request, "baskets/additional_products_detail.html", context=context)

@login_required
def new_cycle(request, cell_slug: str):
    """Used by producer to create new cycles."""
    cell = get_object_or_404(Cell, slug=cell_slug)
    cell_cycles = Cycle.objects.filter(consumer_cell=cell)
    last_cycle = cell_cycles.latest("number") if cell_cycles else None
    last_cycle_number = last_cycle.number if last_cycle else 0

    context = {
        "cell": cell,
    }

    if request.method == "POST":
        cycle_form = CycleForm(request.POST)

        if cycle_form.is_valid():
            cycle = Cycle()
            cycle.number = cycle_form.cleaned_data["number"]
            cycle.begin = cycle_form.cleaned_data["begin"]
            cycle.requests_end = cycle_form.cleaned_data["requests_end"]
            cycle.end = cycle_form.cleaned_data["end"]
            cycle.producer_cell = cell.producer_cell
            cycle.consumer_cell = cell
            cycle.save()

            if last_cycle:
                # Copy product list from previous cycle.
                additional_products_list = AdditionalProductsList.objects.get(cycle=last_cycle)
                products = [product for product in additional_products_list.products.all()]
                additional_products_list.pk = None
                additional_products_list.cycle = cycle
                additional_products_list.save()

                for product in products:
                    product.additional_products_list = additional_products_list
                    product.pk = None
                    product.save()

                return redirect("producer:cell_cycles", cell_slug=cell_slug)

            else:
                return redirect("producer:additional_products_detail", cell_slug=cell_slug, cycle_number=cycle.number)
    else:
        cycle_form = CycleForm(initial={"number": last_cycle_number + 1})
        context["cycle_form"] = cycle_form

    return render(request, "baskets/new_cycle.html", context)

@login_required
def cycle_report_detail(request, cell_slug: str, cycle_number: int):
    """Used by productor."""
    cell = Cell.objects.get(slug=cell_slug)
    cycle = Cycle.objects.get(consumer_cell=cell, number=cycle_number)

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
    cell = Cell.objects.get(slug=cell_slug)

    membership = Membership.objects.filter(person=request.user, cell__cell_type=CellType.PRODUCER.value)

    if not membership:
        return redirect("baskets:home_consumer")

    cycles = Cycle.objects.filter(consumer_cell=cell).order_by("-number")

    context = {
        "cycles": cycles,
        "cell": cell,
    }

    return render(request, "baskets/cell_cycles.html", context=context)


@login_required
def additional_basket_detail(request, basket_uuid: str):
    basket = AdditionalBasket.objects.get(uuid=basket_uuid)
    context = {"basket":basket}
    return render(request, "baskets/basket_detail.html", context=context)


@login_required
def additional_products_list(request, cell_slug: str):
    """Used by consumer."""
    cell = Cell.objects.get(slug=cell_slug)

    context = {
        "closed_cycle": False,
        "cell": cell,
    }
    cycles = Cycle.objects.filter(consumer_cell=cell)

    if not cycles:
        context["closed_cycle"] = True

        return render(request, "baskets/additional_products_list.html", context=context)

    cycle = cycles.latest("number")

    has_basket = AdditionalBasket.objects.filter(cycle=cycle, person=request.user).exists()
    if has_basket:
        return HttpResponse("Pedido de adicionais já realizado para este ciclo.")

    if is_cycle_over(cycle):
        context["is_cycle_over"] = is_cycle_over(cycle)
        context["cycle"] = cycle
        return render(request, "baskets/additional_products_list.html", context=context)

    products_lists = AdditionalProductsList.objects.filter(cycle=cycle)

    if not products_lists:
        context["is_cycle_over"] = is_cycle_over(cycle)
        context["cycle"] = cycle

        return render(request, "baskets/additional_products_list.html", context=context)

    products_list = products_lists.last()
    initial_values = []

    for product in products_list.products.filter(is_available=True):
        initial_values.append({
            "name": product.name,
            "price": product.price,
            "unit": product.unit,
            "requested_quantity": 0,
        })

    if request.method == "POST":
        if is_cycle_over(cycle):
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

                        unit = Unit.objects.get(name=form.cleaned_data["unit"])
                        sold_product.unit = unit

                        sold_product.price = form.cleaned_data["price"]
                        sold_product.requested_quantity = requested_quantity
                        sold_product.basket = additional_basket
                        total_price += sold_product.price * sold_product.requested_quantity
                        sold_product.save()

            additional_basket.total_price = total_price
            additional_basket.save()

            return redirect("baskets:basket_requested", cell_slug=cell_slug, request_uuid=additional_basket.uuid)
        else:
            context["messages"] = basket_formset.non_form_errors()
            render(request, "baskets/additional_products_list.html", context=context)

    basket_formset = BasketFormSet(initial=initial_values)

    context["cycle"] = cycle
    context["cell"] = cell
    context["basket_form"] = basket_formset

    return render(request, "baskets/additional_products_list.html", context=context)


@login_required
def basket_requested(request, cell_slug: str, request_uuid: str):
    cell = get_object_or_404(Cell, slug=cell_slug)
    payment_info = PaymentInfo.objects.filter(cell=cell.producer_cell)
    additional_basket_requested = AdditionalBasket.objects.get(uuid=request_uuid)
    basket_url = additional_basket_requested.get_absolute_url()

    context = {
        "payment_info": payment_info[0] if payment_info else None,
        "cell": cell,
        "total_price": additional_basket_requested.total_price,
        "basket_url": basket_url,
    }
    return render(request, "baskets/basket_requested.html", context)
