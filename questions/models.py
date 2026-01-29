from django.db import models
from tenancy.models import Tenant
from standards.models import StandardVersion, ControlNode as Control

class Question(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    code = models.CharField(max_length=100, blank=True, default="")
    text = models.TextField()
    guidance = models.TextField(blank=True, default="")
    pptdf = models.CharField(max_length=100, blank=True, default="")
    erl_refs = models.TextField(blank=True, default="")  # comma-separated refs
    evidence_hints = models.TextField(blank=True, default="")  # comma-separated

    def __str__(self):
        return self.code or str(self.id)

class QuestionOption(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="options")
    value = models.IntegerField()  # 1-5
    label = models.CharField(max_length=255)

    class Meta:
        unique_together = ("tenant", "question", "value")

class ControlQuestionMap(models.Model):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    standard_version = models.ForeignKey(StandardVersion, on_delete=models.CASCADE)
    control = models.ForeignKey(Control, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    is_mandatory = models.BooleanField(default=True)
    sort_order = models.IntegerField(default=0)

    class Meta:
        unique_together = ("tenant", "standard_version", "control", "question")
