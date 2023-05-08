import datetime
import decimal
from collections import defaultdict
from math import ceil

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.db.models import Sum, Count
from django.http import HttpResponse, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse

from celulas_responsaveis.baskets.forms import ProductsListFormSet, BasketFormSet, WeekCycleForm, MonthCycleForm
from celulas_responsaveis.baskets.models import Basket, ProductsList, MonthCycle, SoldProduct, Unit, WeekCycle, \
    ProductWithPrice, CycleSettings
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
def month_cycle_detail(request, month_identifier: str):
    producer_cell = get_producer_cell(request.user)

    month_date = datetime.datetime.strptime(month_identifier, "%m%Y")
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_cell, begin__month=month_date.month, begin__year=month_date.year).last()

    context = {
        "month_cycle": month_cycle
    }

    return render(request, "baskets/month_cycle_detail.html", context=context)

@login_required
def month_cycles(request):
    """
        Paǵina principal do/a produtora.

    Página que apresenta as células atendendidas pelo grupo de produção para o/a produtora.
    """
    producer_cell = get_producer_cell(request.user)

    month_cycles = MonthCycle.objects.filter(producer_cell=producer_cell)

    context = {
        "month_cycles": month_cycles,
    }

    return render(request, "baskets/month_cycles.html", context=context)

def get_week_of_month(date):
   return ceil(date.day/7.0)

def get_week_cycle(producer_cell):
    cycle_settings = CycleSettings.objects.filter(producer_cell=producer_cell).first()
    today = datetime.date.today()
    week_start_day = today - datetime.timedelta(days=today.weekday())
    delivery_day = week_start_day + datetime.timedelta(days=cycle_settings.week_day_delivery)
    request_day = week_start_day + datetime.timedelta(days=cycle_settings.week_day_requests_end)
    next_delivery_day = delivery_day + datetime.timedelta(days=7)
    next_request_day = request_day + datetime.timedelta(days=7)

    month_cycle = producer_cell.month_cycles.last()
    if not month_cycle:
        month_cycle = MonthCycle()
        month_cycle.producer_cell = producer_cell

        if next_delivery_day.replace(day=1) > delivery_day.replace(day=1):
            begin = week_start_day + datetime.timedelta(days=7)
        else:
            begin = week_start_day
        month_cycle.begin = begin.replace(day=1)
        month_cycle.save()

        week_cycle = WeekCycle()
        week_cycle.month_cycle = month_cycle

        if today > delivery_day:
            week_cycle.delivery_day = next_delivery_day
            week_cycle.request_day = next_request_day
        else:
            week_cycle.delivery_day = delivery_day
            week_cycle.request_day = request_day

        week_cycle.number = get_week_of_month(week_cycle.delivery_day)
        week_cycle.save()

        return week_cycle

    week_cycle = month_cycle.week_cycles.last()

    # Wait one more day before closing current cycle.
    cycle_over_date = week_cycle.delivery_day + datetime.timedelta(days=1)

    if today > cycle_over_date:

        if next_delivery_day.replace(day=1) > week_cycle.delivery_day.replace(day=1):
            month_cycle = MonthCycle()
            month_cycle.producer_cell = producer_cell
            month_cycle.begin = next_delivery_day.replace(day=1)
            month_cycle.save()

        week_cycle = WeekCycle()
        week_cycle.month_cycle = month_cycle
        week_cycle.delivery_day = next_delivery_day
        week_cycle.request_day = next_request_day
        week_cycle.number = get_week_of_month(week_cycle.delivery_day)

        week_cycle.save()

    return week_cycle

@login_required
def producer_home(request):
    producer_cell = get_producer_cell(request.user)
    week_cycle = get_week_cycle(producer_cell)

    week_cycle_infos = week_cycle.baskets.filter(is_paid=True).aggregate(Count('id'), Sum('total_price'))
    paid_baskets = week_cycle.baskets.filter(is_paid=True).count()
    cells_count = producer_cell.consumer_cells.count()

    context = {
        "week_cycle": week_cycle,
        "week_cycle_infos": week_cycle_infos,
        "cells_count": cells_count,
        "paid_baskets": paid_baskets,
    }

    return render(request, "baskets/producer_home.html", context=context)

@login_required
def producer_cycle_requests(request, month_identifier: str, week_cycle_number: int):
    producer_cell = get_producer_cell(request.user)

    month_date = datetime.datetime.strptime(month_identifier, "%m%Y")
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_cell, begin__month=month_date.month, begin__year=month_date.year).last()

    week_cycle = month_cycle.week_cycles.get(number=week_cycle_number)
    baskets = week_cycle.baskets.order_by("-created_date")
    context = {
        "baskets": baskets,
        "week_cycle": week_cycle,
    }
    return render(request, "baskets/producer_requests.html", context=context)

@login_required
def producer_payment_confirmation(request, basket_number: str):
    producer_cell = get_producer_cell(request.user)

    basket = Basket.objects.get(number=basket_number)
    week_cycle = basket.week_cycle

    if request.method == "POST":
        basket.is_paid = True
        basket.save()

    context = {
        "basket": basket,
        "week_cycle": week_cycle,
    }

    return render(request, "baskets/producer_payment_confirmation.html", context=context)

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
            messages.success(request, "Lista salva.")

            return render(request, "baskets/products_list_detail.html", context=context)
        else:
            context["products_list_form"] = products_list_form
            return render(request, "baskets/products_list_detail.html", context=context)

    products_list_form = ProductsListFormSet(instance=products_list)
    context["products_list_form"] = products_list_form

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
            month_cycle.begin = month_cycle_form.cleaned_data["begin"]
            month_cycle.save()

            return  redirect("producer:month_cycles")

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
def week_cycle_total_products(request, month_identifier: str, week_cycle_number: int):
    producer_cell = get_producer_cell(request.user)

    month_date = datetime.datetime.strptime(month_identifier, "%m%Y")
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_cell, begin__month=month_date.month,
                                            begin__year=month_date.year).last()

    week_cycle = month_cycle.week_cycles.get(number=week_cycle_number)

    products = week_cycle.baskets.filter(is_paid=True).values('products__name', 'products__unit__name', 'products__unit__increment', 'products__unit__unit').annotate(requested_quantity=Sum('products__requested_quantity'))
    context = {
        "products": products,
        "week_cycle": week_cycle,
    }
    return render(request, 'baskets/week_cycle_total_products.html', context=context)

@login_required
def week_cycle_report(request, month_identifier: str, week_cycle_number: int):
    producer_cell = get_producer_cell(request.user)

    month_date = datetime.datetime.strptime(month_identifier, "%m%Y")
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_cell, begin__month=month_date.month, begin__year=month_date.year).last()

    week_cycle = month_cycle.week_cycles.get(number=week_cycle_number)

    cells = defaultdict(list)  # Dict[cell_name, List[Baskets]]
    for basket in week_cycle.baskets.filter(is_paid=True):
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
def basket_detail(request, basket_number: str):
    basket = Basket.objects.get(number=basket_number)
    context = {"basket":basket}
    return render(request, "baskets/basket_detail.html", context=context)

@login_required
def basket_detail_edit(request, basket_number: str):
    basket = Basket.objects.get(number=basket_number)

    if is_cycle_over(basket.week_cycle):
        return HttpResponse("Encerrada a alteração de pedidos.")

    products_list = ProductsList.objects.filter(producer_cell=basket.consumer_cell.producer_cell).first()
    actual_products = {product.name: product.requested_quantity for product in basket.products.all()}

    context = {}
    initial_values = []

    for product in products_list.products.filter(is_available=True).order_by("name"):
        requested_quantity = 0
        actual_quantity = actual_products.get(product.name, None)

        if actual_quantity:
            requested_quantity = actual_quantity

        initial_values.append({
            "name": product.name,
            "price": product.price,
            "unit": product.unit,
            "requested_quantity": decimal.Decimal(requested_quantity).to_integral(),
            "product_pk": product.pk,
        })

    if request.method == "POST":
        basket_formset = BasketFormSet(request.POST, initial=initial_values)

        if basket_formset.is_valid():
            total_price = 0.0

            for form in basket_formset:

                if form.is_valid():
                    requested_quantity = form.cleaned_data["requested_quantity"]
                    sold_product = SoldProduct.objects.filter(name=form.cleaned_data["name"], basket=basket).first()

                    if requested_quantity > 0.0:
                        if sold_product:
                            sold_product.requested_quantity = form.cleaned_data["requested_quantity"]
                        else:
                            sold_product = SoldProduct()
                            sold_product.name = form.cleaned_data["name"]
                            sold_product.price = form.cleaned_data["price"]
                            sold_product.requested_quantity = form.cleaned_data["requested_quantity"]
                            sold_product.basket = basket

                            unit = Unit.objects.get(pk=form.unit_pk)
                            sold_product.unit = unit

                        current_product = ProductWithPrice.objects.get(pk=form.initial["product_pk"])
                        current_product.reduce_available_quantity(sold_product.requested_quantity)
                        current_product.save()

                        sold_product.save()
                        if sold_product.unit.increment < 1:
                            total_price += sold_product.price * (sold_product.requested_quantity / 1000)
                        else:
                            total_price += sold_product.price * sold_product.requested_quantity

                    if requested_quantity == 0 and sold_product:
                        sold_product.delete()

            basket.total_price = total_price
            basket.save()
            messages.success(request, "Pedido realizado!")
            return redirect("baskets:basket_requested", request_number=basket.number)
        else:
            context["basket_form"] = basket_formset
            [messages.error(request, error) for error in basket_formset.non_form_errors()]
            context["messages"] = messages.get_messages(request)
            return render(request, "baskets/request_products.html", context=context)


    basket_formset = BasketFormSet(initial=initial_values)
    context = {
        "basket": basket,
        "basket_form": basket_formset,
    }

    return render(request, "baskets/basket_detail_edit.html", context=context)


@login_required
def request_products(request):
    """Used by consumer."""

    consumer_cell = get_consumer_cell(request.user)

    context = {
        "closed_cycle": False,
        "cell": consumer_cell,
        "messages": [],
    }
    month_cycle = MonthCycle.objects.filter(producer_cell=consumer_cell.producer_cell).first()

    if not month_cycle:
        return HttpResponse("Ops, não existem produtos cadastrados.")

    week_cycle = month_cycle.week_cycles.last()

    if not week_cycle:
        return HttpResponse("Ops, não existem produtos cadastrados.")

    current_basket = Basket.objects.filter(week_cycle=week_cycle, person=request.user).first()
    if current_basket:
        messages.success(request, "Você já realizou um pedido.")
        return redirect("baskets:basket_detail", basket_number=current_basket.number)

    products_lists = ProductsList.objects.filter(producer_cell=consumer_cell.producer_cell)

    context["cycle"] = week_cycle
    context["is_cycle_over"] = is_cycle_over(week_cycle)

    if not products_lists or is_cycle_over(week_cycle):
        return render(request, "baskets/request_products.html", context=context)

    products_list = products_lists.first()
    initial_values = []

    for product in products_list.products.filter(is_available=True).order_by("name"):
        initial_values.append({
            "name": product.name,
            "price": product.price,
            "unit": product.unit,
            "requested_quantity": 0,
            "product_pk": product.pk,
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
                        sold_product.price = form.cleaned_data["price"]
                        sold_product.requested_quantity = form.cleaned_data["requested_quantity"]
                        sold_product.basket = additional_basket

                        unit = Unit.objects.get(pk=form.unit_pk)
                        sold_product.unit = unit

                        current_product = ProductWithPrice.objects.get(pk=form.initial["product_pk"])
                        current_product.reduce_available_quantity(sold_product.requested_quantity)
                        current_product.save()
                        sold_product.save()

                        total_price += sold_product.price * sold_product.requested_quantity

            additional_basket.total_price = total_price
            additional_basket.save()
            messages.success(request, "Pedido realizado!")
            return redirect("baskets:basket_requested", request_number=additional_basket.number)
        else:
            context["basket_form"] = basket_formset
            messages.error(request, basket_formset.non_form_errors()[0])
            context["messages"] = messages.get_messages(request)
            return render(request, "baskets/request_products.html", context=context)


    basket_formset = BasketFormSet(initial=initial_values)

    context["cycle"] = week_cycle
    context["cell"] = consumer_cell
    context["basket_form"] = basket_formset

    return render(request, "baskets/request_products.html", context=context)

def get_send_message_url(basket, payment_info):
    from django.utils.http import urlencode

    domain = Site.objects.get_current().domain
    payment_url = reverse("producer:requested_basket_url", kwargs={"basket_number": basket.number})

    text = (
        f"Olá, {payment_info.receiver_name} fiz um pedido de adicionais!\n"
        f"O valor do pedido foi de R${basket.total_price:.2f}\n\n"
        f"Aqui está o comprovante e o link do pedido:\n"
        f"https://{domain}{payment_url}"
    )
    text_encoded = urlencode({"text": text})

    return f"https://wa.me/{payment_info.receiver_contact}?{text_encoded}"

@login_required
def requested_basket_url(request, basket_number: str):
    """
    Redireciona para a confirmação de pagamento se a pessoa que clicou foi um produtor/a ou para
    o detalhes do pedido caso seja consumidor/a.
    """

    try:
        producer_cell = get_producer_cell(request.user)
    except PermissionDenied:
        return redirect("baskets:basket_detail", basket_number=basket_number)
    else:
        return redirect("producer:producer_payment_confirmation", basket_number=basket_number)


@login_required
def basket_requested(request, request_number: str):
    consumer_cell = get_consumer_cell(request.user)
    payment_info = PaymentInfo.objects.filter(producer_cell=consumer_cell.producer_cell).first()
    basket = Basket.objects.get(number=request_number)
    send_payment_confirmation_url = get_send_message_url(basket, payment_info)

    context = {
        "payment_info": payment_info,
        "cell": consumer_cell,
        "basket": basket,
        "send_payment_confirmation_url": send_payment_confirmation_url,
    }
    return render(request, "baskets/basket_requested.html", context)
