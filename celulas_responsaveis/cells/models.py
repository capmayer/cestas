import uuid as uuid

from django.db import models
from django.urls import reverse

from celulas_responsaveis.users.models import User
from celulas_responsaveis.utils.slug_utils import unique_slugify


class ProducerCell(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=False)
    created = models.DateField(auto_now_add=True)
    slug = models.SlugField(max_length=120)
    members = models.ManyToManyField(User, through="ProducerMembership", through_fields=("cell", "person"))

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.name

    def get_management_url(self):
        return reverse("cells:management", kwargs={"cell_slug": self.slug})

    def get_detail_url(self):
        return reverse("cells:producer_cell_detail", kwargs={"cell_slug": self.slug})

    def get_additional_products_list_url(self):
        return reverse("baskets:additional_products_list", kwargs={"cell_slug": self.slug})

    def get_connect_cells_url(self):
        return reverse("cells:connect_cells", kwargs={"cell_slug": self.slug})

    def get_cycles_url(self):
        return reverse("producer:cell_cycles", kwargs={"cell_slug": self.slug})

    def save(self, **kwargs) -> None:
        unique_slugify(self, self.name)
        super(ProducerCell, self).save(**kwargs)


class ConsumerCell(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    share_time = models.CharField(max_length=30, default="")
    message_group_link = models.CharField(max_length=120, default="")
    statute_file = models.FileField(upload_to="cells_statute", blank=True)

    is_active = models.BooleanField(default=False)
    created = models.DateField(auto_now_add=True)
    slug = models.SlugField(max_length=120)
    members = models.ManyToManyField(User, through="ConsumerMembership", through_fields=("cell", "person"))

    producer_cell = models.ForeignKey(ProducerCell, related_name="consumer_cells", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.name

    def get_management_url(self):
        return reverse("cells:management", kwargs={"cell_slug": self.slug})

    def get_detail_url(self):
        return reverse("cells:consumer_cell_detail", kwargs={"cell_slug": self.slug})

    def get_apply_url(self):
        return reverse("cells:apply_to_consumer_cell", kwargs={"cell_slug": self.slug})

    def get_connect_cells_url(self):
        return reverse("cells:connect_cells", kwargs={"cell_slug": self.slug})

    def save(self, **kwargs) -> None:
        unique_slugify(self, self.name)
        super(ConsumerCell, self).save(**kwargs)


class Role(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


class PaymentInfo(models.Model):
    producer_cell = models.ForeignKey(ProducerCell, related_name="payment_info", on_delete=models.CASCADE)
    description = models.TextField()
    receiver_name = models.CharField(max_length=50)
    receiver_contact = models.CharField(max_length=20)
    pix_key = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.producer_cell}"

class ApplicationSurvey(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.is_active}"


class ApplicationQuestion(models.Model):
    application_survey = models.ForeignKey(ApplicationSurvey, related_name="questions", on_delete=models.CASCADE)

    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Application(models.Model):
    cell = models.ForeignKey(ConsumerCell, on_delete=models.CASCADE)
    person = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    created = models.DateField(auto_now_add=True)
    approved_by = models.ForeignKey(User, related_name="+", null=True, on_delete=models.SET_NULL)
    is_pending = models.BooleanField(default=True)
    approved = models.BooleanField(default=False)

    def approve_application_url(self):
        return reverse("cells:approve_application", kwargs={"cell_slug": self.cell.slug, "application_uuid": self.uuid})

    def __str__(self):
        return f"{self.person.email} ({self.is_pending}) -> {self.cell.name}"


class ApplicationAnswer(models.Model):
    application = models.ForeignKey(Application, related_name="survey_answers", on_delete=models.CASCADE)
    question = models.ForeignKey(ApplicationQuestion, null=True, on_delete=models.SET_NULL)
    answer = models.CharField(max_length=255)

    def __str__(self):
        return self.answer


class ConsumerMembership(models.Model):
    cell = models.ForeignKey(ConsumerCell, related_name="+", on_delete=models.CASCADE)
    person = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)
    role = models.ForeignKey(Role, null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    join_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.person.name} ({self.role}) - {self.cell}"


class ProducerMembership(models.Model):
    cell = models.ForeignKey(ProducerCell, related_name="+", on_delete=models.CASCADE)
    person = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)
    role = models.ForeignKey(Role, null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    join_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.person.name} ({self.role}) - {self.cell}"


class CellLocation(models.Model):
    cell = models.ForeignKey(ConsumerCell, related_name="location", on_delete=models.CASCADE)
    address = models.CharField(max_length=100)
    neighborhood = models.CharField(max_length=50)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)

    latitude = models.DecimalField(max_digits=8, decimal_places=5, default=0)
    longitude = models.DecimalField(max_digits=8, decimal_places=5, default=0)

    def __str__(self):
        return f"{self.neighborhood}, {self.city}"

    def get_full_address(self) -> str:
        return f"{self.address}, {self.neighborhood} - {self.city}/{self.state}"
