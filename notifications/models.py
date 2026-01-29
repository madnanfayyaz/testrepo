from django.db import models
from tenancy.models import Tenant

class Notification(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255)
    message = models.TextField()
    status = models.CharField(max_length=50, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)