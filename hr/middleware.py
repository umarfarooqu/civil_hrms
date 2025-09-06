
from django.urls import reverse
from django.shortcuts import redirect

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Only act for authenticated users
        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return None

  # hr/middleware.py


class AdminSuperuserOnlyMiddleware:
    def __init__(self, get_response): self.get_response = get_response
    def __call__(self, request):
        if request.path.startswith("/admin/"):
            if request.user.is_authenticated and not request.user.is_superuser:
                return redirect("/hr/portal/")
        return self.get_response(request)
    # You likely have a flag on the user/employee profile:
        # requires_change = getattr(user, "must_change_password", False)
        # or: getattr(getattr(user, "employee_profile", None), "must_change_password", False)
        requires_change = getattr(user, "must_change_password", False)

        if not requires_change:
            return None

        # Allowed paths (do not block)
        allowed = {
            reverse("login"),
            reverse("logout"),
            reverse("password_change"),
            reverse("portal"),            # allow portal to render
            "/admin/login/",
            "/admin/logout/",
            "/static/",                   # prefixes will be handled below
        }

        path = request.path

        # Allow static files & admin static
        if path.startswith("/static/") or path.startswith("/admin/js/"):
            return None

        # Allow the specific allowed endpoints
        if path in allowed:
            return None

        # Already on password change page?
        if path == reverse("password_change"):
            return None

        # Otherwise, force them to password change
        return redirect("password_change")
