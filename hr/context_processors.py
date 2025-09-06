def dashboard_url(request):
    """
    Decide where the Jazzmin 'Dashboard' link should go:
    - Superusers → /admin/
    - Normal staff/employees → /hr/portal/
    """
    if request.user.is_authenticated and request.user.is_superuser:
        return {"dashboard_url": "/admin/"}
    return {"dashboard_url": "/hr/portal/"}
