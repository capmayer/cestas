from django.contrib.auth.decorators import login_required
from django.contrib.sites.models import Site
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect
from django.urls import reverse

from celulas_responsaveis.baskets.views import get_consumer_membership, get_producer_membership
from celulas_responsaveis.cells.models import PaymentInfo, ConsumerMembership
from celulas_responsaveis.wallets.forms import DepositForm
from celulas_responsaveis.wallets.models import Wallet, Deposit


# Create your views here.

@login_required
def consumer_deposit(request):
    consumer_membership = get_consumer_membership(request.user)
    consumer_cell = consumer_membership.cell
    payment_info = PaymentInfo.objects.filter(producer_cell=consumer_cell.producer_cell).first()

    if request.method == "POST":
        deposit_form = DepositForm(request.POST, request.FILES)

        if deposit_form.is_valid():
            wallet = Wallet.objects.get(person=request.user, producer_cell=consumer_cell.producer_cell)

            deposit = Deposit()
            deposit.wallet = wallet
            deposit.value = deposit_form.cleaned_data["value"]
            deposit.payment_file = request.FILES["payment_file"]

            deposit.save()

            return redirect("wallets:redirect_deposit_confirmation", deposit_number=deposit.number)
    else:
        deposit_form = DepositForm()

    context = {
        "payment_info": payment_info,
        "cell": consumer_cell,
        "deposit_form": deposit_form,
    }
    return render(request, "cells/consumer_deposit.html", context)



def get_deposit_confirmation_message(payment_info, deposit):
    from django.utils.http import urlencode

    domain = Site.objects.get_current().domain
    deposit_confirmation_url = reverse("wallets:redirect_deposit_confirmation", kwargs={"deposit_number": deposit.number})

    text = (
        f"Olá, {payment_info.receiver_name}!\n"
        f"Fiz um pix no valor de R${deposit.value:.2f}\n\n"
        f"Aqui está o comprovante e o link do pedido:\n"
        f"https://{domain}{deposit_confirmation_url}"
    )
    text_encoded = urlencode({"text": text})

    return f"https://wa.me/{payment_info.receiver_contact}?{text_encoded}"



@login_required
def consumer_deposit_detail(request, deposit_number):
    consumer_membership = get_consumer_membership(request.user)
    consumer_cell = consumer_membership.cell
    deposit = Deposit.objects.get(number=deposit_number)
    payment_info = PaymentInfo.objects.get(producer_cell=consumer_cell.producer_cell)
    deposit_confirmation_url = get_deposit_confirmation_message(payment_info, deposit)
    context = {
        "deposit": deposit,
        "deposit_confirmation_url": deposit_confirmation_url,
    }
    return render(request, "cells/consumer_deposit_detail.html", context)


@login_required
def consumer_wallet(request):
    consumer_membership = ConsumerMembership.objects.filter(person=request.user).first()

    wallet = Wallet.objects.get(
        person=request.user,
        producer_cell=consumer_membership.cell.producer_cell,
        consumer_membership=consumer_membership
    )

    context = {
        "wallet": wallet,
    }

    return render(request, "cells/consumer_wallet.html", context=context)


@login_required
def redirect_deposit_confirmation(request, deposit_number):
    """
    Redirect user based on being producer or consumer.
    """

    try:
        producer_membership = get_producer_membership(request.user)
    except PermissionDenied:
        return redirect("wallets:consumer_deposit_detail", deposit_number=deposit_number)
    else:
        return redirect("producer:producer_deposit_confirmation", deposit_number=deposit_number)
