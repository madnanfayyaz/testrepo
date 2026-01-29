from django.db import models
from tenancy.models import Tenant
from assessments.models import Response

class Evidence(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=True, default="")
    uri = models.TextField()  # link or storage key
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, default="UPLOADED")  # UPLOADED/VALIDATED/REJECTED

class ResponseEvidence(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name="evidence_links")
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE)