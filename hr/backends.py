from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from hr.models import Employee
User = get_user_model()

class HRMSIDBackend(ModelBackend):
    def authenticate(self, request, hrms_id=None, username=None, password=None, **kwargs):
        if hrms_id:
            try:
                emp = Employee.objects.select_related("user").get(hrms_id=hrms_id, user__isnull=False)
            except Employee.DoesNotExist:
                return None
            user = emp.user
            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
            return None
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        return None

