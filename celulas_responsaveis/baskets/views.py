import datetime
from collections import defaultdict

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404

from celulas_responsaveis.baskets.forms import ProductsListFormSet, BasketFormSet, WeekCycleForm, MonthCycleForm
from celulas_responsaveis.baskets.models import Basket, ProductsList, MonthCycle, SoldProduct, Unit, WeekCycle
from celulas_responsaveis.cells.models import ConsumerCell, PaymentInfo, ProducerMembership, ConsumerMembership, \
    ProducerCell
from celulas_responsaveis.users.models import User


@login_required
def consumer_home(request):
    baskets = Basket.objects.filter(person=request.user)

    context = {
        "baskets": baskets,
    }
    return render(request, "baskets/home.html", context=context)


def get_active_cycles(cell: ConsumerCell):
    today = datetime.date.today()
    last_week = today + datetime.timedelta(-7)
    return MonthCycle.objects.filter(cell=cell, begin__range=[last_week, today])

def is_cycle_over(cycle: WeekCycle) -> bool:
    today = datetime.date.today()
    return today > cycle.request_day

def get_producer_cell(user: User):
    memberships = ProducerMembership.objects.filter(person=user)

    if not memberships.exists():
        raise PermissionDenied("Você não possui permissão para esta ação")

    return memberships.first().cell

def get_consumer_cell(user: User):
    memberships = ConsumerMembership.objects.filter(person=user)

    if not memberships.exists():
        raise PermissionDenied("Você não possui permissão para esta ação")

    return memberships.first().cell

@login_required
def month_cycle_detail(request, month_cycle_name: str):
    producer_cell = get_producer_cell(request.user)
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_cell, name=month_cycle_name).first()

    context = {
        "month_cycle": month_cycle
    }

    return render(request, "baskets/month_cycle_detail.html", context=context)

@login_required
def producer_home(request):
    """
        Paǵina principal do/a produtora.

    Página que apresenta as células atendendidas pelo grupo de produção para o/a produtora.
    """
    producer_cell = get_producer_cell(request.user)

    month_cycles = MonthCycle.objects.filter(producer_cell=producer_cell)

    context = {
        "month_cycles": month_cycles,
    }

    return render(request, "baskets/producer_home.html", context=context)

@login_required
def products_list_detail(request):
    """Used by producer"""
    producer_cell = get_producer_cell(request.user)
    products_list = ProductsList.objects.filter(producer_cell=producer_cell).first()

    context = dict()
    context["products_list"] = products_list

    if request.method == "POST":
        if not products_list:
            products_list = ProductsList()
            products_list.producer_cell = producer_cell
            products_list.save()

        products_list_form = ProductsListFormSet(request.POST, instance=products_list)

        if products_list_form.is_valid():
            products_list_form.save()
            context["products_list_form"] = products_list_form
            context["messages"] = ["Lista salva."]
            return render(request, "baskets/products_list_detail.html", context=context)
        else:
            context["products_list_form"] = products_list_form
            return render(request, "baskets/products_list_detail.html", context=context)

    additional_products_list_form = ProductsListFormSet(instance=products_list)

    context["products_list_form"] = additional_products_list_form

    return render(request, "baskets/products_list_detail.html", context=context)

@login_required
def new_month_cycle(request):
    producer_cell = get_producer_cell(request.user)
    context = {}

    if request.method == "POST":
        month_cycle_form = MonthCycleForm(request.POST)

        if month_cycle_form.is_valid():
            month_cycle = MonthCycle()
            month_cycle.producer_cell = producer_cell
            month_cycle.name = month_cycle_form.cleaned_data["name"]
            month_cycle.begin = month_cycle_form.cleaned_data["begin"]
            month_cycle.end = month_cycle_form.cleaned_data["end"]

            month_cycle.save()

            return  redirect("producer:producer_home")

    else:
        month_cycle_form = MonthCycleForm()

    context["month_cycle_form"] = month_cycle_form
    return render(request, "baskets/new_month_cycle.html", context)

@login_required
def new_week_cycle(request):
    """
        Used by producer to create a new week cycle.

    Uma vez por semana é necessário criar um novo ciclo semanal para gerenciar os pedidos daquela semana.

    Após criar o ciclo, é feito o redirecionamento para a página de produtos para atualização das quantidades
    disponíveis.

    Esse processo pode ser automatizado no futuro, mas carece debate.
    """
    producer_cell = get_producer_cell(request.user)
    last_month_cycle = producer_cell.month_cycles.last()

    if not last_month_cycle:
        raise Http404("Month cycle not found!")

    last_week_cycle = last_month_cycle.week_cycles.last()

    context = {}

    if request.method == "POST":
        cycle_form = WeekCycleForm(request.POST)

        if cycle_form.is_valid():
            cycle = WeekCycle()
            cycle.number = cycle_form.cleaned_data["number"]
            cycle.delivery_day = cycle_form.cleaned_data["delivery_day"]
            cycle.request_day = cycle_form.cleaned_data["request_day"]
            cycle.month_cycle = last_month_cycle
            cycle.save()

            return redirect("producer:products_list_detail")
    else:
        cycle_number = last_week_cycle.number + 1 if last_week_cycle else 1
        cycle_form = WeekCycleForm(initial={"number": cycle_number})
        context["cycle_form"] = cycle_form

    return render(request, "baskets/new_week_cycle.html", context)

# @login_required
# def consumer_cell_week_cycle_detail(request, cell_slug: str, cycle_number: int):
#     """Used by productor."""
#     cell = ConsumerCell.objects.get(slug=cell_slug)
#     cycle = MonthCycle.objects.get(consumer_cell=cell, number=cycle_number)
#
#     total_cycle_value = 0
#
#     for basket in cycle.baskets.all():
#         total_cycle_value += basket.total_price
#
#     context = {
#         "cycle": cycle,
#         "total_cycle_value": total_cycle_value,
#     }
#
#     return render(request, "baskets/report_detail.html", context=context)


@login_required
def week_cycle_report(request, month_cycle_name: str, week_cycle_number: int):
    producer_cell = get_producer_cell(request.user)
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_cell, name=month_cycle_name).first()
    week_cycle = month_cycle.week_cycles.get(number=week_cycle_number)

    cells = defaultdict(list)  # Dict[cell_name, List[Baskets]]
    for basket in week_cycle.baskets.all():
        cells[basket.consumer_cell].append(basket)

    # Necessary to render the dict in template, otherwise a new empty list is created when template
    # tries to access "items".
    cells.default_factory = None
    context = {
        "cells": cells,
        "week_cycle": week_cycle,
    }

    return render(request, "baskets/report_detail.html", context=context)

@login_required
def basket_detail(request, basket_uuid: str):
    basket = Basket.objects.get(uuid=basket_uuid)
    context = {"basket":basket}
    return render(request, "baskets/basket_detail.html", context=context)


@login_required
def request_products(request):
    """Used by consumer."""

    consumer_cell = get_consumer_cell(request.user)

    context = {
        "closed_cycle": False,
        "cell": consumer_cell,
    }
    month_cycle = MonthCycle.objects.filter(producer_cell=consumer_cell.producer_cell).first()

    if not month_cycle:
        return HttpResponse("Ops, não existem produtos cadastrados.")

    week_cycle = month_cycle.week_cycles.latest("number")

    if not week_cycle:
        return HttpResponse("Ops, não existem produtos cadastrados.")

    has_basket = Basket.objects.filter(week_cycle=week_cycle, person=request.user).exists()
    if has_basket:
        return HttpResponse("Pedido de adicionais já realizado para este ciclo.")

    products_lists = ProductsList.objects.filter(producer_cell=consumer_cell.producer_cell)

    context["cycle"] = week_cycle
    context["is_cycle_over"] = is_cycle_over(week_cycle)

    if not products_lists or is_cycle_over(week_cycle):
        return render(request, "baskets/request_products.html", context=context)

    products_list = products_lists.first()
    initial_values = []

    for product in products_list.products.filter(is_available=True):
        initial_values.append({
            "name": product.name,
            "price": product.price,
            "unit": product.unit,
            "requested_quantity": 0,
        })

    if request.method == "POST":
        if is_cycle_over(week_cycle):
            return HttpResponse("Oops, os pedidos estão encerrados para esse ciclo.")

        basket_formset = BasketFormSet(request.POST, initial=initial_values)

        if basket_formset.is_valid():
            additional_basket = Basket()
            additional_basket.person = request.user
            additional_basket.week_cycle = week_cycle
            additional_basket.consumer_cell = consumer_cell
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

            return redirect("baskets:basket_requested", request_uuid=additional_basket.uuid)
        else:
            context["messages"] = basket_formset.non_form_errors()
            render(request, "baskets/request_products.html", context=context)

    basket_formset = BasketFormSet(initial=initial_values)

    context["cycle"] = week_cycle
    context["cell"] = consumer_cell
    context["basket_form"] = basket_formset

    return render(request, "baskets/request_products.html", context=context)


@login_required
def basket_requested(request, request_uuid: str):
    consumer_cell = get_consumer_cell(request.user)
    payment_info = PaymentInfo.objects.filter(producer_cell=consumer_cell.producer_cell)
    additional_basket_requested = Basket.objects.get(uuid=request_uuid)
    basket_url = additional_basket_requested.get_absolute_url()

    context = {
        "payment_info": payment_info.first() if payment_info else None,
        "cell": consumer_cell,
        "total_price": additional_basket_requested.total_price,
        "basket_url": basket_url,
    }
    return render(request, "baskets/basket_requested.html", context)
