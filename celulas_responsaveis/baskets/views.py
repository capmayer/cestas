import datetime
import decimal
import csv
from collections import defaultdict
from math import ceil

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ViewDoesNotExist
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.utils.timezone import make_aware

from celulas_responsaveis.baskets.forms import BasketFormSet, WeekCycleForm, MonthCycleForm, \
    ProductWithPriceForm, ConsumerBTChoiceForm, StartMonthCycleForm, WeekBasketFormset, WeekBasketForm
from celulas_responsaveis.baskets.models import Basket, ProductsList, MonthCycle, SoldProduct, Unit, WeekCycle, \
    ProductWithPrice, CycleSettings, ConsumerBasketTypeChoice, OfferedBasketType, MonthlyConsumer, PeriodType, \
    WeekBasket
from celulas_responsaveis.cells.models import ProducerMembership, ConsumerMembership, ConsumerCell, Application, \
    ProducerCellSettings
from celulas_responsaveis.users.models import User
from celulas_responsaveis.utils.template_message import consumer_message
from celulas_responsaveis.wallets.models import Deposit, Wallet


@login_required
def consumer_baskets(request):
    baskets = Basket.objects.filter(person=request.user)

    context = {
        "baskets": baskets,
    }
    return render(request, "baskets/consumer/consumer_baskets.html", context=context)

@login_required
def consumer_home(request):
    membership = ConsumerMembership.objects.filter(person=request.user).last()
    pending_application = Application.objects.filter(person=request.user, is_pending=True).last()

    context = {
        "membership": membership,
        "consumer_cell": None,
        "pending_application": pending_application,
    }
    if membership:
        context["consumer_cell"] = membership.cell


    return render(request, "baskets/consumer/home.html", context=context)

def is_cycle_over(cycle: WeekCycle) -> bool:
    """ Used for consumer views. """
    today = timezone.now()
    return today > cycle.request_day + datetime.timedelta(days=1)

def get_producer_membership(user: User):
    memberships = ProducerMembership.objects.filter(person=user)

    if not memberships.exists():
        raise PermissionDenied("Você precisa fazer parte de algum grupo.")

    return memberships.last()

def get_consumer_membership(user: User):
    memberships = ConsumerMembership.objects.filter(person=user)

    if not memberships.exists():
        raise PermissionDenied("Você precisa fazer parte de alguma CCR para realizar essa ação.")

    return memberships.last()

@login_required
def start_month_cycle(request):
    producer_membership = get_producer_membership(request.user)
    producer_cell = producer_membership.cell

    current_month = producer_cell.month_cycles.last()
    month_cycle_form = StartMonthCycleForm(instance=current_month)

    has_members = len(current_month.consumers.all()) > 0
    if has_members:
        messages.error(request, "O ciclo atual já foi iniciado!")

    consumer_cells = ConsumerCell.objects.filter(producer_cell=producer_cell, is_active=True)
    memberships = ConsumerMembership.objects.filter(cell__in=consumer_cells, is_active=True)

    if request.method == "POST" and not has_members:
        month_cycle_form = StartMonthCycleForm(request.POST, instance=current_month)

        if month_cycle_form.is_valid():
            month_cycle = month_cycle_form.save(commit=False)

            offered_baskets = OfferedBasketType.objects.filter(producer_cell=producer_cell)
            offered_basket_to_price = {basket.id: basket.price for basket in offered_baskets}

            for membership in memberships:

                if basket_choice := ConsumerBasketTypeChoice.objects.filter(person=membership.person,
                                                                    consumer_cell=membership.cell).last():
                    price = offered_basket_to_price[basket_choice.offered_basket_type.id]
                    total_price = price * month_cycle.number_of_weeks

                    wallet = membership.wallet.first()
                    wallet.withdraw(total_price)
                    wallet.save()

                    thought_values = {
                        "consumer_basket_choice": basket_choice.offered_basket_type,
                        "consumer_cell": membership.cell,
                        "period": basket_choice.period,
                        "wallet": wallet,
                        "total_price": total_price,
                    }

                    month_cycle.consumers.add(
                        membership.person,
                        through_defaults=thought_values,
                    )

            month_cycle.save()

            return redirect("producer:producer_home")

    context = {
        "current_month": current_month,
        "current_month_form": month_cycle_form,
        "memberships": memberships,
        "membership_to_bc": memberships,
        "has_members": has_members,
    }

    return render(request, "baskets/producer/start_month_cycle.html", context=context)


@login_required
def month_cycle_detail(request, month_identifier: str):
    producer_membership = get_producer_membership(request.user)

    month_date = datetime.datetime.strptime(month_identifier, "%m%Y")
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_membership.cell, begin__month=month_date.month, begin__year=month_date.year).last()

    context = {
        "month_cycle": month_cycle
    }

    return render(request, "baskets/producer/month_cycle_detail.html", context=context)

@login_required
def month_cycles(request):
    """
        Paǵina principal do/a produtora.

    Página que apresenta as células atendendidas pelo grupo de produção para o/a produtora.
    """
    producer_membership = get_producer_membership(request.user)

    month_cycles = MonthCycle.objects.filter(producer_cell=producer_membership.cell).order_by("begin__month")

    context = {
        "month_cycles": month_cycles,
    }

    return render(request, "baskets/producer/month_cycles.html", context=context)

def get_week_of_month(date):
   return ceil(date.day/7.0)

def get_week_cycle(producer_cell):
    cycle_settings = CycleSettings.objects.filter(producer_cell=producer_cell).first()
    today = timezone.now().astimezone(timezone.get_default_timezone())
    today = today.replace(hour=0, minute=0)

    # Get monday.
    week_start_day = today - datetime.timedelta(days=today.weekday())

    delivery_day = week_start_day + datetime.timedelta(days=cycle_settings.week_day_delivery)
    request_day = week_start_day + datetime.timedelta(days=cycle_settings.week_day_requests_end) + datetime.timedelta(hours=cycle_settings.week_day_requests_end_time.hour)

    next_delivery_day = delivery_day + datetime.timedelta(days=7)
    next_request_day = request_day + datetime.timedelta(days=7)

    month_cycle = producer_cell.month_cycles.last()
    if not month_cycle:
        month_cycle = MonthCycle()
        month_cycle.producer_cell = producer_cell

        # Check if next delivery day is in the next month.
        if next_delivery_day.replace(day=1) > delivery_day.replace(day=1):
            month_cycle.begin = next_delivery_day.replace(day=1)
        else:
            month_cycle.begin = delivery_day.replace(day=1)

        month_cycle.save()

        week_cycle = WeekCycle()
        week_cycle.month_cycle = month_cycle

        if today > delivery_day:
            week_cycle.delivery_day = next_delivery_day.date()
            week_cycle.request_day = next_request_day
        else:
            week_cycle.delivery_day = delivery_day.date()
            week_cycle.request_day = request_day

        week_cycle.number = get_week_of_month(week_cycle.delivery_day)
        week_cycle.save()
        return week_cycle

    week_cycle = month_cycle.week_cycles.last()
    # Wait one more day before closing current cycle.
    cycle_over_date = week_cycle.delivery_day + datetime.timedelta(days=1)

    if today.date() > cycle_over_date:

        # Check if next delivery day is in next month.
        if next_delivery_day.date().replace(day=1) > week_cycle.delivery_day.replace(day=1):
            month_cycle = MonthCycle()
            month_cycle.producer_cell = producer_cell
            month_cycle.begin = next_delivery_day.replace(day=1)
            month_cycle.save()

        week_cycle = WeekCycle()
        week_cycle.month_cycle = month_cycle
        week_cycle.delivery_day = next_delivery_day.date()
        week_cycle.request_day = next_request_day
        week_cycle.number = get_week_of_month(next_delivery_day)

        week_cycle.save()

    return week_cycle

@login_required
def producer_home(request):
    producer_membership = get_producer_membership(request.user)
    producer_cell = producer_membership.cell
    current_month = producer_cell.month_cycles.last()
    current_week = producer_cell.current_week

    today = timezone.now()
    today = today.replace(hour=0, minute=0)

    deposits = Deposit.objects.filter(wallet__producer_cell=producer_cell, confirmed=False).aggregate(Sum("value"))
    wallets = Wallet.objects.filter(producer_cell=producer_cell).aggregate(Sum("current_balance"))

    context = {
        "pending_deposits_sum": deposits["value__sum"],
        "wallets_balance": wallets["current_balance__sum"],
        "create_new_week": False,
        "create_new_month": False,
        "alert_start_month_cycle": False,
    }

    if current_month is None:
        context["create_new_month"] = True
        return render(request, "baskets/producer/home.html", context=context)

    if current_month.begin.replace(day=10) < today.date() and len(current_month.consumers.all()) <= 0:
        context["alert_start_month_cycle"] = True
    if current_week is None or current_week.delivery_day + datetime.timedelta(days=1) < today.date():
        context["create_new_week"] = True

    if current_week:
        context["week_cycle_infos"] = current_week.baskets.all().aggregate(Count('id'), Sum('total_price'))

    context["current_month"] = current_month
    context["week_cycle"] = current_week

    return render(request, "baskets/producer/home.html", context=context)

@login_required
def producer_cycle_requests(request, month_identifier: str, week_cycle_number: int):
    producer_membership = get_producer_membership(request.user)

    month_date = datetime.datetime.strptime(month_identifier, "%m%Y")
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_membership.cell, begin__month=month_date.month, begin__year=month_date.year).last()

    week_cycle = month_cycle.week_cycles.get(number=week_cycle_number)
    baskets = week_cycle.baskets.order_by("-created_date")
    context = {
        "baskets": baskets,
        "week_cycle": week_cycle,
    }
    return render(request, "baskets/producer/baskets_requested.html", context=context)


@login_required
def producer_week_cycle_detail(request, month_identifier: str, week_cycle_number: int):
    producer_cell = get_producer_membership(request.user).cell
    month_date = datetime.datetime.strptime(month_identifier, "%m%Y")
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_cell, begin__month=month_date.month,
                                            begin__year=month_date.year).last()

    week_cycle = month_cycle.week_cycles.get(number=week_cycle_number)
    week_info = week_cycle.baskets.all().aggregate(Count('id'), Sum('total_price'))

    context = {
        "week_cycle": week_cycle,
        "week_cycle_info": week_info,
    }
    return render(request, "baskets/producer/week_cycle_detail.html", context=context)


@login_required
def producer_edit_week_cycle(request, month_identifier: str, week_cycle_number: int):
    producer_cell = get_producer_membership(request.user).cell
    month_date = datetime.datetime.strptime(month_identifier, "%m%Y")
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_cell, begin__month=month_date.month,
                                            begin__year=month_date.year).last()

    week_cycle = month_cycle.week_cycles.get(number=week_cycle_number)

    if request.method == 'POST':
        cycle_form = WeekCycleForm(request.POST)

        if cycle_form.is_valid():
            week_cycle.number = cycle_form.cleaned_data['number']
            request_time = cycle_form.cleaned_data['request_time']

            new_request_day = week_cycle.request_day - datetime.timedelta(week_cycle.request_day.weekday() - int(cycle_form.cleaned_data["request_day"]))
            new_request_day = datetime.datetime(new_request_day.year, new_request_day.month, new_request_day.day, request_time.hour, request_time.minute)
            week_cycle.request_day = new_request_day

            new_delivery_day = week_cycle.delivery_day - datetime.timedelta(week_cycle.delivery_day.weekday() - int(cycle_form.cleaned_data["delivery_day"]))
            week_cycle.delivery_day = new_delivery_day

            week_cycle.save()

        return redirect('producer:producer_home')
    else:
        current_data = {
            "number": week_cycle.number,
            "delivery_day": week_cycle.delivery_day.weekday(),
            "request_time": week_cycle.request_day.astimezone(),
            "request_day": week_cycle.request_day.astimezone().weekday(),
        }
        cycle_form = WeekCycleForm(initial=current_data)

    week_basket = WeekBasket.objects.filter(week=week_cycle).first()

    context = {
        "cycle_form":cycle_form,
        "week_cycle": week_cycle,
        "week_basket": week_basket,
    }
    return render(request, "baskets/producer/edit_week_cycle.html", context=context)


@login_required
def producer_list_consumers(request):
    producer_membership = get_producer_membership(request.user)

    consumers = ConsumerMembership.objects.filter(cell__producer_cell=producer_membership.cell)

    context = {
        "consumers": consumers
    }

    return render(request, "baskets/producer_list_consumers.html", context=context)

@login_required
def producer_deposit_confirmation(request, deposit_number: str):
    producer_membership = get_producer_membership(request.user)

    deposit = Deposit.objects.get(number=deposit_number)

    if request.method == "POST":
        wallet = deposit.wallet
        wallet.deposit(deposit.value)
        wallet.save()

        deposit.confirmed = True
        deposit.rejected = False
        deposit.save()

    context = {
        "deposit": deposit,
    }

    return render(request, "baskets/producer/producer_deposit_confirmation.html", context=context)

@login_required
def producer_deposit_reject(request, deposit_number: str):
    producer_membership = get_producer_membership(request.user)

    deposit = Deposit.objects.get(number=deposit_number)

    if request.method == "POST":
        deposit.rejected = True

        if deposit.confirmed:
            wallet = deposit.wallet
            wallet.withdraw(deposit.value)
            wallet.save()

            deposit.confirmed = False

        deposit.save()

    context = {
        "deposit": deposit,
    }

    return render(request, "baskets/producer/producer_deposit_confirmation.html", context=context)


@login_required
def producer_cells_list(request):
    producer_membership = get_producer_membership(request.user)
    site_domain = Site.objects.get_current().domain  # Necessary to show full url.
    context = {
        "producer_cell": producer_membership.cell,
        "site_domain": site_domain,
    }

    return render(request, "baskets/producer/cells_list.html", context=context)

@login_required
def producer_product_delete(request, product_id):
    producer_membership = get_producer_membership(request.user)
    product = ProductWithPrice.objects.get(id=product_id)
    if producer_membership.cell == product.additional_products_list.producer_cell:
        product.delete()
        messages.success(request, f"{product.name} deletado!")

    return redirect("producer:products_list_detail")

@login_required
def products_list_detail(request):
    """Used by producer"""
    producer_membership = get_producer_membership(request.user)
    producer_cell = producer_membership.cell
    products_list = ProductsList.objects.filter(producer_cell=producer_cell).first()

    context = dict()

    if products_list is None:
        products_list = ProductsList()
        products_list.producer_cell = producer_cell
        products_list.save()

    context["products_list"] = products_list

    return render(request, "baskets/producer/products_list_detail.html", context=context)

@login_required
def producer_product_detail(request, product_id):
    producer_membership = get_producer_membership(request.user)
    product = ProductWithPrice.objects.get(id=product_id)

    if request.method == "POST":
        product_form = ProductWithPriceForm(request.POST, instance=product)

        if product_form.is_valid():
            product = product_form.save(commit=False)
            product.save()
            messages.success(request, f"{product.name} alterado!")

        return redirect("producer:products_list_detail")

    product_form = ProductWithPriceForm(instance=product)
    context = {
        "product_form": product_form,
        "product": product,
    }

    return render(request, "baskets/producer/product_detail.html", context=context)


@login_required
def producer_new_product(request):
    producer_membership = get_producer_membership(request.user)

    if request.method == "POST":
        product_form = ProductWithPriceForm(request.POST)

        if product_form.is_valid():
            product_list = ProductsList.objects.get(producer_cell=producer_membership.cell)

            product = product_form.save(commit=False)
            product.additional_products_list = product_list
            product.save()

            messages.success(request, f"{product.name} adicionado!")

        return redirect("producer:products_list_detail")

    product_form = ProductWithPriceForm()
    context = {
        "product_form": product_form,

    }

    return render(request, "baskets/producer/product_add.html", context=context)


@login_required
def new_month_cycle(request):
    producer_membership = get_producer_membership(request.user)
    producer_cell = producer_membership.cell
    consumer_cells = ConsumerCell.objects.filter(producer_cell=producer_cell, is_active=True)
    memberships = ConsumerMembership.objects.filter(cell__in=consumer_cells, is_active=True)

    current_month = producer_cell.month_cycles.last()
    month_is_over = current_month.is_over() if current_month else False

    context = {
        "memberships": memberships,
        "number_of_consumers": len(memberships),
        "month_is_over": month_is_over,
    }
    today = timezone.now()

    if request.method == "POST":
        month_cycle_form = MonthCycleForm(request.POST)

        if month_cycle_form.is_valid():
            month_cycle = MonthCycle()
            month_cycle.producer_cell = producer_membership.cell

            begin_date = today.replace(day=month_cycle_form.cleaned_data["begin"])

            month_cycle.begin = begin_date
            month_cycle.number_of_weeks = month_cycle_form.cleaned_data["number_of_weeks"]
            month_cycle.save()

            offered_baskets = OfferedBasketType.objects.filter(producer_cell=producer_membership.cell)
            offered_basket_to_price = {basket.id: basket.price for basket in offered_baskets}

            for membership in memberships:
                if basket_choice := ConsumerBasketTypeChoice.objects.filter(person=membership.person, consumer_cell=membership.cell).last():
                    price = offered_basket_to_price[basket_choice.offered_basket_type.id]
                    total_price = price * month_cycle.number_of_weeks

                    wallet = membership.wallet.first()
                    wallet.withdraw(total_price)
                    wallet.save()

                    thought_values = {
                        "consumer_basket_choice": basket_choice.offered_basket_type,
                        "consumer_cell": membership.cell,
                        "period": basket_choice.period,
                        "wallet": wallet,
                        "total_price": total_price,
                    }

                    month_cycle.consumers.add(
                        membership.person,
                        through_defaults=thought_values,
                    )

            month_cycle.save()
            return  redirect("producer:new_week_cycle")
    else:
        month_cycle_form = MonthCycleForm()

    context["month_cycle_form"] = month_cycle_form
    return render(request, "baskets/producer/new_month_cycle.html", context)

@login_required
def new_week_cycle(request):
    """
        Used by producer to create a new week cycle.

    Uma vez por semana é necessário criar um novo ciclo semanal para gerenciar os pedidos daquela semana.

    Após criar o ciclo, é feito o redirecionamento para a página de produtos para atualização das quantidades
    disponíveis.

    Esse processo pode ser automatizado no futuro, mas carece debate.
    """
    producer_membership = get_producer_membership(request.user)
    producer_cell = producer_membership.cell
    current_month = producer_cell.month_cycles.last()

    today = timezone.now()
    # Occurs only in setup producer account.
    if current_month is None:
        current_month = MonthCycle()
        current_month.begin = today.replace(day=10)
        current_month.producer_cell = producer_cell
        current_month.save()
    else:
        next_month = (current_month.begin.month + 1) % 12 or 12
        if current_month.begin.replace(month=next_month) < today.date():
            current_month = MonthCycle()
            current_month.begin = today.replace(day=10)
            current_month.producer_cell = producer_cell
            current_month.save()

    context = {
        "month_cycle": current_month,
    }

    if request.method == "POST":
        cycle_form = WeekCycleForm(request.POST)

        if cycle_form.is_valid():
            current_week = WeekCycle()
            current_week.number = cycle_form.cleaned_data["number"]

            def get_weekday_date(week_day: int):
                return today.date() + datetime.timedelta(days=week_day - today.weekday())

            request_day = get_weekday_date(int(cycle_form.cleaned_data["request_day"]))
            current_week.request_day = request_day
            current_week.delivery_day = get_weekday_date(int(cycle_form.cleaned_data["delivery_day"]))
            current_week.month_cycle = current_month

            if current_week.request_day < today.date():
                current_week.request_day += datetime.timedelta(days=7)
                current_week.delivery_day += datetime.timedelta(days=7)

            current_week.save()

            return redirect("producer:products_list_detail")

    else:
        initial_cycle = {
            "number": 1,
        }

        if current_week := producer_cell.current_week:
            initial_cycle["delivery_day"] = current_week.delivery_day.weekday()
            initial_cycle["request_time"] = current_week.request_day.astimezone()
            initial_cycle["request_day"] = current_week.request_day.astimezone().weekday()
            initial_cycle["number"] = current_week.number + 1

        cycle_form = WeekCycleForm(initial=initial_cycle)
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
    producer_membership = get_producer_membership(request.user)

    month_date = datetime.datetime.strptime(month_identifier, "%m%Y")
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_membership.cell, begin__month=month_date.month,
                                            begin__year=month_date.year).last()

    week_cycle = month_cycle.week_cycles.get(number=week_cycle_number)

    def format_requested_quantity(product):
        unit = Unit.objects.get(pk=product["products__unit_id"])
        requested_quantity = product["requested_quantity"]
        if requested_quantity >= 1000 or unit.unit =="g":
            formatted_quantity = f"{requested_quantity / 1000} {unit.k_unit}"
            formatted_number = requested_quantity / 1000
        else:
            formatted_quantity = f"{int(requested_quantity)} {unit.unit}"
            formatted_number = requested_quantity

        product["formatted_requested_quantity"] = formatted_quantity
        product["formatted_number_quantity"] = formatted_number
        return product

    products = week_cycle.baskets.all().values('products__name', 'products__unit_id', 'products__price').annotate(requested_quantity=Sum('products__requested_quantity'))
    products = [format_requested_quantity(product) for product in products]

    for product in products:
        total_price = product['formatted_number_quantity'] * product['products__price']
        formatted_total_price = "{:.2f}".format(total_price)
        product['total_price_product'] = formatted_total_price

    context = {
        "products": products,
        "week_cycle": week_cycle,
    }

    if request.method == 'POST' and request.POST.get('download_csv'):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=produtosvendidos.csv'

        # Create a csv writer
        writer = csv.writer(response)

        # Add column headings
        writer.writerow(['Nome', 'Quantidade', 'Valor Total'])

        # Loop through the content
        for product in products:
            writer.writerow([product['products__name'], product['requested_quantity'], product['total_price_product']])


        return response

    return render(request, 'baskets/week_cycle_total_products.html', context=context)

@login_required
def week_cycle_report(request, month_identifier: str, week_cycle_number: int):
    producer_membership = get_producer_membership(request.user)

    month_date = datetime.datetime.strptime(month_identifier, "%m%Y")
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_membership.cell, begin__month=month_date.month, begin__year=month_date.year).last()

    week_cycle = month_cycle.week_cycles.get(number=week_cycle_number)

    cells = defaultdict(list)  # Dict[cell_name, List[Baskets]]
    for basket in week_cycle.baskets.order_by("person__name"):
        cells[basket.consumer_cell].append(basket)

    # Necessary to render the dict in template, otherwise a new empty list is created when template
    # tries to access "items".
    cells.default_factory = None
    context = {
        "cells": cells,
        "week_cycle": week_cycle,
    }

    return render(request, "baskets/producer/week_cycle_report.html", context=context)


@login_required
def new_week_basket(request):
    producer_membership = get_producer_membership(request.user)
    producer_cell = producer_membership.cell
    current_week = producer_cell.current_week

    week_basket = WeekBasket.objects.filter(week=current_week).first()

    if week_basket is None:
        week_basket = WeekBasket()
        week_basket.week = current_week
        week_basket.save()

    week_basket_form = WeekBasketForm(request.POST or None, instance=week_basket)
    week_basket_formset = WeekBasketFormset(request.POST or None, instance=week_basket)

    context = {
        "week_basket_formset": week_basket_formset,
        "current_week": current_week,
    }

    if request.method == "POST":
        if week_basket_formset.is_valid() and week_basket_form.is_valid():
            week_basket_form.save()
            week_basket_formset.save()

            current_week.week_basket_defined = True
            current_week.save()

            messages.success(request, "Produtos salvos")
            context["week_basket_form"] = week_basket_formset
            return render(request, "baskets/producer/new_week_basket.html", context=context)

        context["week_basket_form"] = week_basket_form
        return render(request, "baskets/producer/new_week_basket.html", context=context)

    return render(request, "baskets/producer/new_week_basket.html", context=context)


@login_required
def week_cycle_baskets(request, month_identifier: str, week_cycle_number: int):
    producer_membership = get_producer_membership(request.user)
    producer_cell = producer_membership.cell
    producer_settings = ProducerCellSettings.objects.get(cell=producer_cell)

    month_date = datetime.datetime.strptime(month_identifier, "%m%Y")
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_membership.cell, begin__month=month_date.month, begin__year=month_date.year).first()

    week_cycle = month_cycle.week_cycles.filter(number=week_cycle_number).first()
    allowed_periods = [PeriodType.Weekly]
    if producer_settings.biweekly_baskets is True and week_cycle.number % 2 != 0:
        allowed_periods.append(PeriodType.Biweekly)

    monthly_consumers = MonthlyConsumer.objects.filter(month_cycle=month_cycle, period__in=allowed_periods).order_by("consumer_cell")
    offered_basket_types = OfferedBasketType.objects.filter(producer_cell=month_cycle.producer_cell)

    basket_types_sum = {}
    for offered_basket_type in offered_basket_types:
        basket_types_sum[offered_basket_type.name] = monthly_consumers.filter(consumer_basket_choice=offered_basket_type).count()

    context = {
        "offered_basket_types": offered_basket_types,
        "consumers": monthly_consumers,
        "basket_types_sum": basket_types_sum,
        "week_cycle": week_cycle,
    }

    return render(request, "baskets/producer/week_cycle_baskets.html", context=context)


@login_required
def basket_detail(request, basket_number: str):
    basket = Basket.objects.get(number=basket_number)
    context = {
        "basket": basket,
        "is_cycle_over": is_cycle_over(basket.week_cycle),
    }
    return render(request, "baskets/consumer/basket_detail.html", context=context)

@login_required
def basket_detail_edit(request, basket_number: str):
    basket = Basket.objects.get(number=basket_number)

    if request.user != basket.person:
        raise PermissionDenied("Opss, está cesta é de outra pessoa.")

    context = {
        "basket": basket,
        "cycle": basket.week_cycle,
        "cell": basket.consumer_cell,
    }

    if is_cycle_over(basket.week_cycle):
        return consumer_message(request, "Alterações encerradas.")

    products_list = ProductsList.objects.filter(producer_cell=basket.consumer_cell.producer_cell).first()
    actual_products = {product.name: product.requested_quantity for product in basket.products.all()}

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
                        current_product = ProductWithPrice.objects.get(pk=form.initial["product_pk"])

                        if sold_product:
                            current_product.add_available_quantity(sold_product.requested_quantity)
                            sold_product.requested_quantity = form.cleaned_data["requested_quantity"]
                        else:
                            sold_product = SoldProduct()
                            sold_product.name = form.cleaned_data["name"]
                            sold_product.price = form.cleaned_data["price"]
                            sold_product.requested_quantity = form.cleaned_data["requested_quantity"]
                            sold_product.basket = basket

                            unit = Unit.objects.get(pk=form.unit_pk)
                            sold_product.unit = unit


                        current_product.reduce_available_quantity(sold_product.requested_quantity)
                        current_product.save()

                        if sold_product.unit.increment < 1:
                            total_price += sold_product.price * (sold_product.requested_quantity / 1000)
                        else:
                            total_price += sold_product.price * sold_product.requested_quantity

                        sold_product.save()

                    if requested_quantity == 0 and sold_product:
                        sold_product.delete()

            difference = total_price - basket.total_price
            if difference > 0:
                basket.wallet.withdraw(abs(difference))
            else:
                basket.wallet.deposit(abs(difference))

            basket.wallet.save()
            basket.total_price = total_price
            basket.save()
            messages.success(request, "Pedido alterado!")
            return redirect("baskets:basket_requested", request_number=basket.number)
        else:
            context["basket_form"] = basket_formset
            [messages.error(request, error) for error in basket_formset.non_form_errors()]
            context["messages"] = messages.get_messages(request)
            return render(request, "baskets/consumer/request_products.html", context=context)


    basket_formset = BasketFormSet(initial=initial_values)
    context["basket_form"] = basket_formset

    return render(request, "baskets/consumer/request_products_change.html", context=context)


@login_required
def request_products(request):
    """Used by consumer."""

    consumer_membership = get_consumer_membership(request.user)
    consumer_cell = consumer_membership.cell

    if not consumer_membership.is_active:
        raise PermissionDenied("Sua participação está inativa.")

    context = {
        "closed_cycle": False,
        "cell": consumer_cell,
        "messages": [],
    }
    month_cycle = MonthCycle.objects.filter(producer_cell=consumer_cell.producer_cell).last()
    if not month_cycle:
        raise PermissionDenied("O ciclo deste mês ainda não foi iniciado.")

    week_cycle = month_cycle.week_cycles.last()

    if not week_cycle:
        raise PermissionDenied("Os pedidos adicionais não foram abertos.")

    current_basket = Basket.objects.filter(week_cycle=week_cycle, person=request.user).first()
    if current_basket:
        messages.success(request, "Você já realizou um pedido.")
        return redirect("baskets:basket_detail", basket_number=current_basket.number)

    products_lists = ProductsList.objects.filter(producer_cell=consumer_cell.producer_cell)

    if not products_lists.exists():
        raise PermissionDenied("O produtor ainda não registrou produtos.")

    context["cycle"] = week_cycle
    context["is_cycle_over"] = is_cycle_over(week_cycle)

    if is_cycle_over(week_cycle):
        return render(request, "baskets/consumer/request_products.html", context=context)

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
            return consumer_message(request,"Os pedidos foram encerrados.")

        basket_formset = BasketFormSet(request.POST, initial=initial_values)

        if basket_formset.is_valid():
            wallet = Wallet.objects.get(person=request.user, producer_cell=consumer_cell.producer_cell)

            additional_basket = Basket()
            additional_basket.wallet = wallet
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

                        if sold_product.unit.increment < 1:
                            total_price += sold_product.price * (sold_product.requested_quantity / 1000)
                        else:
                            total_price += sold_product.price * sold_product.requested_quantity

                        sold_product.save()

            additional_basket.total_price = total_price
            additional_basket.save()

            additional_basket.wallet.withdraw(additional_basket.total_price)
            additional_basket.wallet.save()

            messages.success(request, "Pedido enviado!")
            return redirect("baskets:basket_requested", request_number=additional_basket.number)
        else:
            context["basket_form"] = basket_formset
            [messages.error(request, error) for error in basket_formset.non_form_errors()]
            context["messages"] = messages.get_messages(request)
            return render(request, "baskets/consumer/request_products.html", context=context)


    basket_formset = BasketFormSet(initial=initial_values)

    context["cycle"] = week_cycle
    context["cell"] = consumer_cell
    context["basket_form"] = basket_formset

    return render(request, "baskets/consumer/request_products.html", context=context)


@login_required
def basket_requested(request, request_number: str):
    consumer_membership = get_consumer_membership(request.user)
    consumer_cell = consumer_membership.cell
    basket = Basket.objects.get(number=request_number)

    context = {
        "cell": consumer_cell,
        "basket": basket,
    }
    return render(request, "baskets/consumer/basket_requested.html", context)


@login_required
def consumers_list(request):
    producer_membership = get_producer_membership(request.user)

    pending_applications = Application.objects.filter(cell__in=producer_membership.cell.consumer_cells.all(), is_pending=True)

    wallets = Wallet.objects.filter(producer_cell=producer_membership.cell).order_by("current_balance")

    context = {
        "wallets": wallets,
        "pending_applications": pending_applications,
        "producer_cells": producer_membership.cell,
    }

    return render(request, "baskets/producer/consumers_list.html", context=context)


@login_required
def consumer_detail(request, consumer_username):
    producer_membership = get_producer_membership(request.user)

    user = get_object_or_404(User, username=consumer_username)
    wallet = Wallet.objects.get(person=user, producer_cell=producer_membership.cell)
    consumer_membership = wallet.consumer_membership
    consumer_bt_choice = ConsumerBasketTypeChoice.objects.filter(person=user, consumer_cell=consumer_membership.cell).last()

    context = {
        "wallet": wallet,
        "membership": consumer_membership,
        "consumer_bt_choice": consumer_bt_choice,
    }

    return render(request, "baskets/producer/consumer_detail.html", context=context)


@login_required
def consumer_wallet(request, consumer_username):
    producer_membership = get_producer_membership(request.user)

    wallet = Wallet.objects.get(person__username=consumer_username, producer_cell=producer_membership.cell)

    context = {
        "wallet": wallet
    }

    if request.method == "POST":
        if wallet.current_balance < 0:
            deposit = Deposit()
            deposit.wallet = wallet
            deposit.value = wallet.absolute_current_balance
            deposit.confirmed = True
            deposit.save()

            wallet.deposit(deposit.value)
            wallet.save()

            messages.success(request, "Saldo quitado com sucesso!")

        else:
            messages.error(request, "O saldo da caderneta é positivo. Operação só pode ser realizada para saldos negativos.")

    return render(request, "baskets/producer/consumer_wallet.html", context=context)

@login_required
def consumers_deposits(request):
    producer_membership = get_producer_membership(request.user)
    producer_cell = producer_membership.cell

    pending_deposits = Deposit.objects.filter(wallet__producer_cell=producer_cell, confirmed=False, rejected=False).order_by("created_date")
    other_deposits = Deposit.objects.filter(wallet__producer_cell=producer_cell, confirmed=True) | Deposit.objects.filter(wallet__producer_cell=producer_cell, rejected=True)

    context = {
        "pending_deposits": pending_deposits,
        "other_deposits": other_deposits.order_by("created_date")[:20],
    }

    return render(request, "baskets/producer/consumers_deposits.html", context=context)
