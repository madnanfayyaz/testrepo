from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/tenancy/", include("tenancy.urls")),
    path("api/iam/", include("iam.urls")),
    path("api/standards/", include("standards.urls")),
    path("api/question-bank/", include("question_bank.urls")),
    path("api/assessments/", include("assessments.urls")),
    path("api/responses/", include("responses.urls")),
    path("api/findings/", include("findings.urls")),
    path("api/reporting/", include("reporting.urls")),
]
