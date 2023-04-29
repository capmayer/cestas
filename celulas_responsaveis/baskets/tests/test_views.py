import pytest

from celulas_responsaveis.baskets.models import CycleSettings
from celulas_responsaveis.baskets.views import get_week_cycle
from celulas_responsaveis.cells.models import ProducerCell

pytestmark = pytest.mark.django_db

@pytest.fixture
def producer_cell():
    producer_cell = ProducerCell()
    producer_cell.name = "CCR Centro"
    producer_cell.slug = "ccr-centro"
    producer_cell.save()

    yield producer_cell

def test_get_week_cycle(producer_cell, freezer):
    cycle_settings = CycleSettings()
    cycle_settings.producer_cell = producer_cell
    cycle_settings.week_day_requests_end = 3
    cycle_settings.week_day_delivery = 4
    cycle_settings.save()

    current_week = get_week_cycle(producer_cell)
    assert current_week.delivery_day.month == 4


    assert producer_cell.name == "CCR Centro"
