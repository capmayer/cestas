from django.urls import resolve, reverse

from celulas_responsaveis.users.models import User


def test_detail(user: User):
    assert (
        reverse("users:detail", kwargs={"username": user.username})
        == f"/pessoas/{user.username}/"
    )
    assert resolve(f"/pessoas/{user.username}/").view_name == "users:detail"


def test_update():
    assert reverse("users:update") == "/pessoas/~update/"
    assert resolve("/pessoas/~update/").view_name == "users:update"


def test_redirect():
    assert reverse("users:redirect") == "/pessoas/~redirect/"
    assert resolve("/pessoas/~redirect/").view_name == "users:redirect"
