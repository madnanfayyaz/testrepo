from django.db import models
from tenancy.models import Tenant
from questions.models import Question

class PolicyDocument(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    uri = models.TextField()  # future: S3/MinIO key
    created_at = models.DateTimeField(auto_now_add=True)

class QuestionPolicyReference(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="policy_refs")
    policy_document = models.ForeignKey(PolicyDocument, on_delete=models.CASCADE)
    note = models.CharField(max_length=255, blank=True, default="")