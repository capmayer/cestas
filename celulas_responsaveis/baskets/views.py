import datetime
import decimal
from collections import defaultdict
from math import ceil

from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied, ViewDoesNotExist
from django.db.models import Sum, Count
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone

from celulas_responsaveis.baskets.forms import BasketFormSet, WeekCycleForm, MonthCycleForm, \
    ProductWithPriceForm, ConsumerBTChoiceForm
from celulas_responsaveis.baskets.models import Basket, ProductsList, MonthCycle, SoldProduct, Unit, WeekCycle, \
    ProductWithPrice, CycleSettings, ConsumerBasketTypeChoice, OfferedBasketType, MonthlyConsumer
from celulas_responsaveis.cells.models import ProducerMembership, ConsumerMembership, ConsumerCell
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
    membership = ConsumerMembership.objects.filter(person=request.user).first()

    context = {
        "membership": membership,
        "consumer_cell": None
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

    return memberships.first()

def get_consumer_membership(user: User):
    memberships = ConsumerMembership.objects.filter(person=user)

    if not memberships.exists():
        raise PermissionDenied("Você precisa fazer parte de alguma CCR para realizar essa ação.")

    return memberships.first()

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
    current_week = producer_cell.current_week

    today = timezone.now()
    today = today.replace(hour=0, minute=0)

    if current_week is None or current_week.delivery_day + datetime.timedelta(days=1) <= today.date():
        return redirect("producer:new_week_cycle")

    week_cycle_infos = current_week.baskets.all().aggregate(Count('id'), Sum('total_price'))
    deposits = Deposit.objects.filter(wallet__producer_cell=producer_cell, confirmed=False).aggregate(Sum("value"))
    wallets = Wallet.objects.filter(producer_cell=producer_cell).aggregate(Sum("current_balance"))

    context = {
        "week_cycle": current_week,
        "week_cycle_infos": week_cycle_infos,
        "pending_deposits_sum": deposits["value__sum"],
        "wallets_balance": wallets["current_balance__sum"],
    }

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

def producer_edit_week_cycle(request, week_id: int):
    producer_cell = get_producer_membership(request.user).cell
    week_cycle = WeekCycle.objects.get(id = week_id)

    if request.method == 'POST':
        cycle_form = WeekCycleForm(request.POST)

        if cycle_form.is_valid():
            week_cycle.number = cycle_form.cleaned_data['number']
            
            new_request_day = week_cycle.request_day - datetime.timedelta(week_cycle.request_day.weekday() - int(cycle_form.cleaned_data["request_day"]))
            request_time = cycle_form.cleaned_data['request_time']
            week_cycle.request_day = datetime.datetime(new_request_day.year, new_request_day.month, new_request_day.day, request_time.hour, request_time.minute)
            new_delivery_day = week_cycle.delivery_day - datetime.timedelta(week_cycle.delivery_day.weekday() - int(cycle_form.cleaned_data["delivery_day"]))
            week_cycle.delivery_day = new_delivery_day
        
            week_cycle.save()

        return redirect('producer:producer_home')
    else:
        current_data = {
            'number': week_cycle.number
        }
        
        current_data["delivery_day"] = week_cycle.delivery_day.weekday()
        current_data["request_time"] = week_cycle.request_day.time()
        current_data["request_day"] = week_cycle.request_day.weekday()
        current_data["number"] = week_cycle.number 

        cycle_form = WeekCycleForm(initial = current_data)

    context = {
        'cycle_form':cycle_form,
        'week_cycle': week_cycle
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
    context = {}

    consumer_cells = ConsumerCell.objects.filter(producer_cell=producer_membership.cell)
    memberships = ConsumerMembership.objects.filter(cell__in=consumer_cells, is_active=True)

    context["memberships"] = memberships
    context["number_of_consumers"] = len(context["memberships"])

    if request.method == "POST":
        month_cycle_form = MonthCycleForm(request.POST)

        if month_cycle_form.is_valid():
            month_cycle = MonthCycle()
            month_cycle.producer_cell = producer_membership.cell

            today = timezone.now()
            begin_date = today.replace(day=month_cycle_form.cleaned_data["begin"])

            month_cycle.begin = begin_date
            month_cycle.number_of_weeks = month_cycle_form.cleaned_data["number_of_weeks"]
            month_cycle.save()

            offered_baskets = OfferedBasketType.objects.filter(producer_cell=producer_membership.cell)
            offered_basket_to_price = {basket.id: basket.price for basket in offered_baskets}

            for membership in memberships:
                consumer_basket_choice = ConsumerBasketTypeChoice.objects.filter(person=membership.person, consumer_cell=membership.cell)
                if consumer_basket_choice.exists():
                    basket_choice = consumer_basket_choice.first()
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
    if current_month is None:
        return redirect("producer:new_month_cycle")

    next_month = (current_month.begin.month + 1) % 12 or 12
    if current_month.begin.replace(month=next_month) < today.date():
        return redirect("producer:new_month_cycle")

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
            initial_cycle["request_time"] = current_week.request_day.time()
            initial_cycle["request_day"] = current_week.request_day.weekday()
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
        if requested_quantity >= 1000:
            formatted_quantity = f"{requested_quantity / 1000} {unit.k_unit}"
        else:
            formatted_quantity = f"{int(requested_quantity)} {unit.unit}"

        product["formatted_requested_quantity"] = formatted_quantity
        return product

    products = week_cycle.baskets.all().values('products__name', 'products__unit_id', 'products__price').annotate(requested_quantity=Sum('products__requested_quantity'))
    products = [format_requested_quantity(product) for product in products]

    for product in products:
        product['total_price_product'] = product['requested_quantity'] * product['products__price']


    context = {
        "products": products,
        "week_cycle": week_cycle,
    }
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
def week_cycle_baskets(request, month_identifier: str, week_cycle_number: int):
    producer_membership = get_producer_membership(request.user)

    month_date = datetime.datetime.strptime(month_identifier, "%m%Y")
    month_cycle = MonthCycle.objects.filter(producer_cell=producer_membership.cell, begin__month=month_date.month, begin__year=month_date.year).first()

    monthly_consumers = MonthlyConsumer.objects.filter(month_cycle=month_cycle).order_by("consumer_cell")
    offered_basket_types = OfferedBasketType.objects.filter(producer_cell=month_cycle.producer_cell)

    basket_types_sum = {}
    for offered_basket_type in offered_basket_types:
        basket_types_sum[offered_basket_type.name] = monthly_consumers.filter(consumer_basket_choice=offered_basket_type).count()

    context = {
        "offered_basket_types":offered_basket_types,
        "consumers": monthly_consumers,
        "week_cycle": producer_membership.cell.current_week,
        "basket_types_sum": basket_types_sum,
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
def consumers_wallets(request):
    producer_membership = get_producer_membership(request.user)

    wallets = Wallet.objects.filter(producer_cell=producer_membership.cell).order_by("current_balance")

    context = {
        "wallets": wallets,
        "producer_cells": producer_membership.cell,
    }

    return render(request, "baskets/producer/consumers_wallets.html", context=context)

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

    deposits = Deposit.objects.filter(wallet__producer_cell=producer_cell, confirmed=False).order_by("created_date")
    confirmed_deposits = Deposit.objects.filter(wallet__producer_cell=producer_cell, confirmed=True).order_by("created_date")[:10]
    context = {
        "deposits": deposits,
        "confirmed_deposits": confirmed_deposits,
    }

    return render(request, "baskets/producer/consumers_deposits.html", context=context)
