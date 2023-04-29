from factory import Faker, post_generation
from factory.django import DjangoModelFactory

from celulas_responsaveis.baskets.models import Basket


class BasketFactory(DjangoModelFactory):
    class Meta:
        model = Basket

    name = Faker("name")
