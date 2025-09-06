from django.urls import path
from . import views

# app_name optional; keep it if you might namespace later
app_name = "hr"

urlpatterns = [
    path("", views.home, name="hr-home"),                   # /hr/
    path("portal/", views.portal, name="portal"),           # /hr/portal/
    path("portal/profile/", views.profile, name="employee-profile"),

    # 📸 photo upload/change
    

    # Admin-only search/export
    path("search/", views.search, name="search"),
    path("export/csv/", views.export_csv, name="export-csv"),
    path("export/excel/", views.export_excel, name="export-excel"),
    path("export/pdf/", views.export_pdf, name="export-pdf"),

    # Self-service sections
    path("portal/education/", views.portal_education),
    path("portal/postings/", views.portal_postings),
    path("portal/deputations/", views.portal_deputations),
    path("portal/apar/", views.portal_apar),
    path("portal/property/", views.portal_property),
    path("portal/trainings/", views.portal_trainings),
    path("portal/awards/", views.portal_awards),
    path("portal/pay/", views.portal_pay),
    path("portal/increments/", views.portal_increments),
    path("portal/leaves/", views.portal_leaves),
    path("portal/allegations/", views.portal_allegations),
]
