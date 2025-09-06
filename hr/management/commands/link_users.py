from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hr.models import Employee

DEFAULT_PASSWORD = "umars123@"

class Command(BaseCommand):
    help = "Create/link Django users for Employees (username = hrms_id). Default password = umars123@, must be changed on first login."

    def handle(self, *args, **options):
        created = 0
        for emp in Employee.objects.filter(user__isnull=True).exclude(hrms_id__isnull=True).exclude(hrms_id=""):
            hrms = emp.hrms_id.strip()
            if not hrms:
                continue
            user, _ = User.objects.get_or_create(username=hrms, defaults={"email": emp.email or ""})
            # Set default password always if new user
            user.set_password(DEFAULT_PASSWORD)
            user.save()
            emp.user = user
            emp.save()
            created += 1
            self.stdout.write(f"Created user for {emp.name} ({hrms}) password={DEFAULT_PASSWORD}")
        self.stdout.write(self.style.SUCCESS(f"Linked {created} employee(s)."))

