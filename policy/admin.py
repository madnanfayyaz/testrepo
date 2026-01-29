from django.contrib import admin
from .models import PolicyDocument, QuestionPolicyReference

admin.site.register(PolicyDocument)
admin.site.register(QuestionPolicyReference)