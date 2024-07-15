from django.db import models
from django.core.exceptions import ValidationError
from django.urls import reverse

class Activite(models.Model):
    activite = models.CharField(max_length=200)
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    object = models.TextField(blank=True, null=True)
    document = models.FileField(upload_to='documents/', blank=True, null=True)
    contact = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)

    def clean(self):
        if self.date_fin < self.date_debut:
            raise ValidationError("La date de fin ne peut pas être antérieure à la date de début.")

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    @property
    def get_html_url(self):
        url = reverse('event_detail', args=(self.id,))
        return f'<a href="{url}"> {self.activite} </a>'

    def __str__(self):
        return self.activite