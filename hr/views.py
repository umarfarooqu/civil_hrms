# hr/views.py
from __future__ import annotations

from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required, user_passes_test
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.urls import reverse
from django.core.exceptions import ValidationError
from .forms import EmployeeSelfEditForm

from .models import Employee, SelfEditPermission
from .forms import (
    EducationFS, PostingFS, DeputationFS, AparFS, PropertyFS, TrainingFS,
    AwardFS, PayFS, IncrementFS, LeaveFS, AllegationFS
)

# Map portal sections -> SelfEditPermission boolean fields
PERM_MAP = {
    "education": "education",
    "postings": "postings",
    "deputations": "deputations",
    "apar": "apar",
    "property": "property",
    "trainings": "trainings",
    "awards": "awards",
    "pay": "pay",
    "increments": "increments",
    "leaves": "leaves",
    "allegations": "allegations",
}

# === Optional HRMS login form support ===========================
try:
    from .auth_forms import HRMSAuthenticationForm as HRMSLoginForm
except Exception:
    HRMSLoginForm = None


def login_with_hrms(request):
    """
    Optional dedicated HRMS login view.
    If unused, rely on /login/ configured in urls.py.
    """
    if request.user.is_authenticated:
        return redirect("portal")

    if HRMSLoginForm is None:
        messages.error(request, "Login form not available. Please use /login/ or contact admin.")
        return redirect("portal")

    form = HRMSLoginForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        # support either 'identifier' or 'hrms_id' depending on your form
        hrms_id = (form.cleaned_data.get("hrms_id") or form.cleaned_data.get("identifier") or "").strip()
        password = form.cleaned_data.get("password") or ""
        try:
            emp = Employee.objects.select_related("user").get(hrms_id=hrms_id, user__isnull=False)
        except Employee.DoesNotExist:
            messages.error(request, "Invalid HRMS ID or account not linked. Please contact admin.")
        else:
            user = authenticate(request, username=emp.user.username, password=password)
            if user:
                login(request, user)
                return redirect("portal")
            messages.error(request, "Invalid password.")
    return render(request, "registration/login.html", {"form": form})


# === Common helpers =============================================
def _is_staff(user): 
    return user.is_staff or user.is_superuser


def home(request):
    return render(request, "home.html")


def _filtered_qs(request):
    qs = Employee.objects.all()
    hrms = (request.GET.get("hrms_id") or "").strip()
    branch = (request.GET.get("branch") or "").strip()
    college = (request.GET.get("college") or "").strip()
    if hrms:
        qs = qs.filter(hrms_id__icontains=hrms)
    if branch:
        qs = qs.filter(branch__icontains=branch)
    if college:
        qs = qs.filter(college_name__icontains=college)
    return qs.order_by("hrms_id")


# === Admin-only search/exports ==================================
@user_passes_test(_is_staff)
def search(request):
    qs = _filtered_qs(request)
    return render(request, "search.html", {"qs": qs})


import csv, io, pandas as pd
from xhtml2pdf import pisa


@user_passes_test(_is_staff)
def export_csv(request):
    qs = _filtered_qs(request)
    resp = HttpResponse(content_type="text/csv")
    resp["Content-Disposition"] = "attachment; filename=employees.csv"
    w = csv.writer(resp)
    w.writerow(["HRMS", "Name", "Designation", "Branch", "College", "Posting"])
    for e in qs:
        w.writerow([e.hrms_id, e.name, e.current_designation, e.branch, e.college_name, e.present_posting])
    return resp


@user_passes_test(_is_staff)
def export_excel(request):
    qs = _filtered_qs(request)
    data = [{
        "HRMS": e.hrms_id,
        "Name": e.name,
        "Designation": e.current_designation,
        "Branch": e.branch,
        "College": e.college_name,
        "Posting": e.present_posting,
    } for e in qs]
    df = pd.DataFrame(data)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Employees")
    resp = HttpResponse(
        buf.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp["Content-Disposition"] = "attachment; filename=employees.xlsx"
    return resp


@user_passes_test(_is_staff)
def export_pdf(request):
    qs = _filtered_qs(request)
    html = render_to_string("report.html", {"qs": qs})
    buf = io.BytesIO()
    pisa.CreatePDF(src=html, dest=buf)
    resp = HttpResponse(buf.getvalue(), content_type="application/pdf")
    resp["Content-Disposition"] = "attachment; filename=employees.pdf"
    return resp


# === Employee self-service portal ================================
@login_required
def portal(request):
    emp = getattr(request.user, "employee_profile", None)
    return render(request, "portal.html", {"employee": emp})


def _resolve_model_from_formset(FS):
    """
    Resolve the model class for a given formset class (works for ModelFormSet or InlineFormSet).
    """
    model = getattr(FS, "model", None)
    if model is not None:
        return model
    form_cls = getattr(FS, "form", None)
    model = getattr(getattr(form_cls, "_meta", None), "model", None)
    return model


def _portal_formset(request, FS, title, code=None):
    """
    Generic handler for all self-edit sections.
    - Restricts queryset to the logged-in employee
    - Enforces SelfEditPermission
    - Edits only non-APPROVED rows; APPROVED rows are shown read-only below
    - On save, flips rows to PENDING and clears approval fields
    """
    emp = getattr(request.user, 'employee_profile', None)
    if not emp:
        return redirect('portal')

    # Permission check
    perm = getattr(emp, 'self_edit_perm', None)
    allowed = True
    if code and perm is not None:
        allowed = getattr(perm, PERM_MAP.get(code, ''), False)
    if not allowed:
        return HttpResponseForbidden('Editing this section is disabled. Contact admin.')

    # If no edit permission — show read-only list of all rows
    Model = FS.model
    if code:
        perm = getattr(emp, 'self_edit_perm', None)
        if perm is not None and not getattr(perm, PERM_MAP.get(code, ''), False):
            base_qs_ro = Model.objects.filter(employee=emp).order_by('-id')
            return render(request, 'readonly_list.html', {
                'title': title,
                'rows': base_qs_ro,
            })

    # Build queryset & split approved vs editable
    Model = FS.model
    base_qs = Model.objects.filter(employee=emp)
    if hasattr(Model, 'status'):
        edit_qs = base_qs.exclude(status='APPROVED')
        approved_qs = base_qs.filter(status='APPROVED').order_by('-id')
    else:
        edit_qs = base_qs
        approved_qs = Model.objects.none()

    if request.method == 'POST':
        formset = FS(request.POST, request.FILES, queryset=edit_qs)
        # Hide approval fields from forms
        for f in formset.forms:
            for fld in ('employee','status','approved_by','approved_at','reviewer_remark'):
                if fld in f.fields:
                    f.fields[fld].widget = f.fields[fld].hidden_widget()
        if formset.is_valid():
            instances = formset.save(commit=False)
            # Prevent deleting APPROVED via formset
            for obj in formset.deleted_objects:
                if hasattr(obj, 'status') and obj.status == 'APPROVED':
                    continue  # ignore delete for approved
                obj.delete()
            for inst in instances:
                inst.employee = emp
                if hasattr(inst, 'status'):
                    inst.status = 'PENDING'
                    if hasattr(inst, 'approved_by'): inst.approved_by = None
                    if hasattr(inst, 'approved_at'): inst.approved_at = None
                    if hasattr(inst, 'reviewer_remark'): inst.reviewer_remark = ''
                inst.save()
            messages.success(request, 'Saved successfully. Pending items will require admin approval.')
            return redirect(request.path)
    else:
        formset = FS(queryset=edit_qs)
        for f in formset.forms:
            for fld in ('employee','status','approved_by','approved_at','reviewer_remark'):
                if fld in f.fields:
                    f.fields[fld].widget = f.fields[fld].hidden_widget()
    return render(request, 'formset.html', {
        'formset': formset,
        'title': title,
        'approved_qs': approved_qs,
    })


@login_required
def portal_education(request):   return _portal_formset(request, EducationFS, "My Education", code="education")

@login_required
def portal_postings(request):    return _portal_formset(request, PostingFS, "My Postings", code="postings")

@login_required
def portal_deputations(request): return _portal_formset(request, DeputationFS, "My Deputations", code="deputations")

@login_required
def portal_apar(request):        return _portal_formset(request, AparFS, "My APAR", code="apar")

@login_required
def portal_property(request):    return _portal_formset(request, PropertyFS, "My Property Returns", code="property")

@login_required
def portal_trainings(request):   return _portal_formset(request, TrainingFS, "My Trainings", code="trainings")

@login_required
def portal_awards(request):      return _portal_formset(request, AwardFS, "My Awards", code="awards")

@login_required
def portal_pay(request):         return _portal_formset(request, PayFS, "My Pay Scale Changes", code="pay")

@login_required
def portal_increments(request):  return _portal_formset(request, IncrementFS, "My Advance Increments", code="increments")

@login_required
def portal_leaves(request):      return _portal_formset(request, LeaveFS, "My Leaves", code="leaves")

@login_required
def portal_allegations(request): return _portal_formset(request, AllegationFS, "My Allegations", code="allegations")


@login_required
def profile(request):
    emp = getattr(request.user, "employee_profile", None)
    if not emp:
        messages.error(request, "Employee profile not linked to your account.")
        return redirect("portal")

    if request.method == "POST":
        form = EmployeeSelfEditForm(request.POST, request.FILES, instance=emp)
        if form.is_valid():
            try:
                # models.py enforces: HRMS-based filename, overwrite, old-file cleanup, ≤30 KB
                form.save()
                messages.success(request, "Photo updated successfully.")
                try:
                    return redirect("hr:employee-profile")   # if hr.urls is namespaced
                except Exception:
                    return redirect("employee-profile")      # fallback if not namespaced
            except ValidationError as e:
                # if model.clean/save raised (e.g., >30 KB), surface it on the form
                form.add_error("photo", e.message_dict.get("photo", e.messages if hasattr(e, "messages") else e))
    else:
        form = EmployeeSelfEditForm(instance=emp)

    return render(request, "employee/profile.html", {"employee": emp, "form": form})

