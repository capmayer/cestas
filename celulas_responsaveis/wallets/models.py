from dataclasses import dataclass
from random import randrange

from django.db import models
from django.utils import timezone

from celulas_responsaveis.cells.models import ProducerCell, ConsumerMembership
from celulas_responsaveis.users.models import User


@dataclass
class Registry:
    name: str
    number: str
    date: str
    value: float
    debt: bool
    pendent: bool = False


class Wallet(models.Model):
    person = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)
    consumer_membership = models.ForeignKey(ConsumerMembership, related_name="wallet", on_delete=models.CASCADE)
    producer_cell = models.ForeignKey(ProducerCell, related_name="+", on_delete=models.CASCADE)
    current_balance = models.FloatField(default=0)

    @property
    def absolute_current_balance(self) -> float:
        return abs(self.current_balance)

    def check_balance(self):
        confirmed_deposits = self.deposits.filter(confirmed=True)

        deposits_value = sum([deposit.value for deposit in confirmed_deposits])
        baskets_value = sum([basket.total_price for basket in self.baskets.all()])
        month_cycles = sum([cycle.total_price for cycle in self.month_cycles.all()])

        self.current_balance = deposits_value - baskets_value - month_cycles

    def withdraw(self, value: float):
        self.current_balance = self.current_balance - value

    def deposit(self, value: float):
        self.current_balance = self.current_balance + value

    def ordered_registries(self):
        deposits = self.deposits.order_by("-created_date")[:10]
        baskets = self.baskets.order_by("-created_date")[:10]
        month_cycles = self.month_cycles.order_by("-created_date")[:10]

        deposit_entries = [Registry(name="Transferência", number=deposit.number, date=deposit.created_date, value=deposit.value, debt=False, pendent=not deposit.confirmed) for deposit in deposits]
        basket_entries = [Registry(name="Cesta adicionais", number=basket.number, date=basket.created_date, value=basket.total_price, debt=True) for basket in baskets]
        month_cycles_entries = [Registry(name=f"Ciclo {cycle.month_cycle}", number=cycle.number, date=cycle.created_date, value=cycle.total_price, debt=True) for cycle in month_cycles]

        entries = deposit_entries + basket_entries + month_cycles_entries

        return sorted(entries, key=lambda entry: entry.date, reverse=True)[:10]


def deposit_identification_number():
    time_now = timezone.now()
    random_number = randrange(0, 10**6)
    identification = f"{random_number:06d}{time_now.day:02d}{time_now.month:02d}{time_now.year:04d}"
    return identification

class Deposit(models.Model):
    number = models.CharField(default=deposit_identification_number, editable=False, unique=True, max_length=20)
    wallet = models.ForeignKey(Wallet, related_name="deposits", on_delete=models.CASCADE)
    value = models.FloatField()
    confirmed = models.BooleanField(default=False)
    created_date = models.DateTimeField(auto_now_add=True)

