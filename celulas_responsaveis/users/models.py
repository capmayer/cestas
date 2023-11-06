from enum import Enum

from django.contrib.auth.models import AbstractUser
from django.db.models import CharField
from django.urls import reverse
from datetime import datetime
from django.utils.translation import gettext_lazy as _

class UserViewer(Enum):
    CONSUMER = "CS"
    PRODUCER = "PD"

class User(AbstractUser):
    """
    Default custom user model for Células Responsáveis.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    #: First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore
    phone_number = CharField(blank=True, max_length=10)
    cep = CharField(blank=True, max_length=8)
    address = CharField(blank=True, max_length=255)
    city = CharField(blank=True, max_length=100)
    state = CharField(blank=True, max_length=2)

    VIEW_CHOICES = (
        (UserViewer.CONSUMER.value, "Consumer"),
        (UserViewer.PRODUCER.value, "Producer"),
    )
    viewing_as = CharField(choices=VIEW_CHOICES, default=UserViewer.CONSUMER.value, max_length=3)

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})

    def get_greetings(self):
        hour = datetime.now().hour
        greeting = "Boa noite"
        if 5 <= hour < 12:
            greeting = "Bom dia"
        elif 12 <= hour < 18:
            greeting = "Boa tarde"

        return f"{greeting}, {self.name.split(' ')[0]}"

    def is_producer(self) -> bool:
        return self.viewing_as == UserViewer.PRODUCER.value
