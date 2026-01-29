from django.core.management.base import BaseCommand
from tenancy.models import Tenant
from iam.models import Role
from standards.models import Standard, StandardVersion, ControlNode as Control
from questions.models import Question, QuestionOption

class Command(BaseCommand):
    help = "Seed initial tenant, roles, and minimal demo content (standard + 1 question with 1-5 options)."

    def add_arguments(self, parser):
        parser.add_argument("--tenant-name", required=True)

    def handle(self, *args, **opts):
        tenant, _ = Tenant.objects.get_or_create(name=opts["tenant_name"])

        # Roles
        for r in ["Admin", "Compliance Officer", "Responder", "Reviewer", "Auditor"]:
            Role.objects.get_or_create(tenant=tenant, name=r)

        # Minimal demo library content (safe to delete later)
        std, _ = Standard.objects.get_or_create(tenant=tenant, name="Demo Standard", defaults={"code": "DEMO"})
        ver, _ = StandardVersion.objects.get_or_create(tenant=tenant, standard=std, version="1.0", defaults={"is_active": True})
        ctrl, _ = Control.objects.get_or_create(tenant=tenant, standard_version=ver, code="DEMO-1", defaults={"title": "Demo Control"})

        q, _ = Question.objects.get_or_create(
            tenant=tenant,
            code="Q-DEMO-1",
            defaults={
                "text": "Demo question: Rate the implementation (1-5).",
                "guidance": "Use 1=Not implemented, 5=Optimized.",
            },
        )
        for v, label in [
            (1, "1 - Not Implemented"),
            (2, "2 - Partially Implemented"),
            (3, "3 - Implemented"),
            (4, "4 - Managed"),
            (5, "5 - Optimized"),
        ]:
            QuestionOption.objects.get_or_create(tenant=tenant, question=q, value=v, defaults={"label": label})

        self.stdout.write(self.style.SUCCESS("Seed completed (tenant, roles, demo standard/control/question/options)."))
