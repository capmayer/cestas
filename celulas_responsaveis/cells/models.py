import uuid as uuid
from django.db import models
from django.urls import reverse

from celulas_responsaveis.users.models import User
from celulas_responsaveis.utils.slug_utils import unique_slugify


class Cell(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_active = models.BooleanField(default=False)
    created = models.DateField(auto_now_add=True)
    slug = models.SlugField(max_length=120)
    members = models.ManyToManyField(User, through="Membership", through_fields=("cell", "person"))

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("cells:cell_detail", kwargs={"cell_slug": self.slug})

    def get_additional_products_list_url(self):
        return reverse("baskets:additional_products_list", kwargs={"cell_slug": self.slug})

    def get_apply_url(self):
        return reverse("cells:consumer_apply", kwargs={"cell_slug": self.slug})

    def save(self, **kwargs) -> None:
        unique_slugify(self, self.name)
        super(Cell, self).save(**kwargs)


class Role(models.Model):
    name = models.CharField(max_length=30)

    def __str__(self):
        return self.name


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
    cell = models.ForeignKey(Cell, on_delete=models.CASCADE)
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


class Membership(models.Model):
    cell = models.ForeignKey(Cell, related_name="+", on_delete=models.CASCADE)
    person = models.ForeignKey(User, related_name="+", on_delete=models.CASCADE)
    role = models.ForeignKey(Role, null=True, on_delete=models.SET_NULL)
    is_active = models.BooleanField(default=True)
    join_date = models.DateField(auto_now_add=True)

    class Meta:
        permissions = [
            ("approve_applications", "Can approve applications."),
            ("can_edit", "Can edit cell information."),
        ]

    def __str__(self):
        return f"{self.person.name} ({self.role}) - {self.cell}"


class CellLocation(models.Model):
    cell = models.ForeignKey(Cell, on_delete=models.CASCADE)

    address = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=50)

    latitude = models.DecimalField(max_digits=8, decimal_places=5)
    longitude = models.DecimalField(max_digits=8, decimal_places=5)
