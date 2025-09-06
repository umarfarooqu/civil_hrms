from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from django import forms
from django.utils.html import format_html
from . import models
from .resources import EmployeeResource

# Try to use shared max size if present in models; fallback to 30 KB
try:
    from .models import MAX_PHOTO_BYTES
except Exception:
    MAX_PHOTO_BYTES = 30 * 1024  # 30 KB

ALLOWED_CTYPES = {"image/jpeg", "image/jpg", "image/png", "image/pjpeg"}

# -----------------------------
# Masters
# -----------------------------
@admin.register(models.College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("name", "code")
    search_fields = ("name", "code")


# -----------------------------
# Inlines
# -----------------------------
class InlineBase(admin.TabularInline):
    extra = 0

class EducationInline(InlineBase):        model = models.Education
class PostingInline(InlineBase):          model = models.Posting
class DeputationInline(InlineBase):       model = models.Deputation
class AparInline(InlineBase):             model = models.Apar
class PropertyReturnInline(InlineBase):   model = models.PropertyReturn
class TrainingInline(InlineBase):         model = models.Training
class AwardInline(InlineBase):            model = models.Award
class PayScaleInline(InlineBase):         model = models.PayScaleChange
class AdvanceIncrementInline(InlineBase): model = models.AdvanceIncrement
class LeaveInline(InlineBase):            model = models.LeaveRecord
class AllegationInline(InlineBase):       model = models.Allegation


# -----------------------------
# Employee Admin
# -----------------------------
class SelfEditPermissionInline(admin.StackedInline):
    model = models.SelfEditPermission
    can_delete = False
    extra = 0


class EmployeeAdminForm(forms.ModelForm):
    class Meta:
        model = models.Employee
        fields = "__all__"
        widgets = {
            "photo": forms.ClearableFileInput(attrs={
                "accept": "image/jpeg,image/png",
            })
        }

    def clean_photo(self):
        f = self.cleaned_data.get("photo")
        if not f:
            return f
        # Size limit
        if getattr(f, "size", 0) > MAX_PHOTO_BYTES:
            kb = MAX_PHOTO_BYTES // 1024
            raise forms.ValidationError(f"Photo must be ≤ {kb} KB.")
        # Content type check
        ctype = (getattr(f, "content_type", "") or "").lower()
        if ctype and ctype not in ALLOWED_CTYPES:
            raise forms.ValidationError("Only JPEG or PNG images are allowed.")
        return f


@admin.register(models.Employee)
class EmployeeAdmin(ImportExportModelAdmin):
    resource_class = EmployeeResource
    form = EmployeeAdminForm
    readonly_fields = ("photo_preview",)

    # Prefer FK display; gracefully fall back to legacy text fields
    def college_display(self, obj):
        return obj.college.name if getattr(obj, "college", None) else (obj.college_name or "")
    college_display.short_description = "College"

    def present_posting_display(self, obj):
        return obj.present_posting_college.name if getattr(obj, "present_posting_college", None) else (obj.present_posting or "")
    present_posting_display.short_description = "Present Posting"

    # Photo thumbnail column
    def photo_thumb(self, obj):
        if getattr(obj, "photo", None):
            try:
                return format_html(
                    '<img src="{}" style="height:40px;width:40px;object-fit:cover;'
                    'border-radius:50%;border:1px solid #ddd;" />', obj.photo.url
                )
            except Exception:
                return "—"
        return "—"
    photo_thumb.short_description = "Photo"

    # Large preview on change page (readonly)
    def photo_preview(self, obj):
        if getattr(obj, "photo", None):
            try:
                return format_html(
                    '<img src="{}" style="height:160px;border-radius:12px;'
                    'border:1px solid #eee;object-fit:cover;" />', obj.photo.url
                )
            except Exception:
                return "—"
        return "—"
    photo_preview.short_description = "Preview"

    list_display = (
        "civil_list_no",
        "hrms_id",
        "name",
        "photo_thumb",
        "current_designation",
        "college_display",
        "present_posting_display",
        "branch",
    )
    search_fields = (
        "hrms_id",
        "name",
        # legacy text fields
        "college_name",
        "present_posting",
        "branch",
        # new FK lookups
        "college__name",
        "present_posting_college__name",
    )
    list_filter = (
        "college",
        "present_posting_college",
        "current_designation",
        "branch",
    )
    autocomplete_fields = (
        "college",
        "present_posting_college",
    )
    inlines = [
        SelfEditPermissionInline,
        EducationInline, PostingInline, DeputationInline,
        AparInline, PropertyReturnInline, TrainingInline,
        AwardInline, PayScaleInline, AdvanceIncrementInline,
        LeaveInline, AllegationInline
    ]


# -----------------------------
# Register remaining models with Import/Export
# -----------------------------
class BaseIE(ImportExportModelAdmin):
    pass

for m in [
    models.Education, models.Posting, models.Deputation, models.Apar,
    models.PropertyReturn, models.Training, models.Award,
    models.PayScaleChange, models.AdvanceIncrement, models.LeaveRecord,
    models.Allegation,
]:
    admin.site.register(m, BaseIE)


# -----------------------------
# SelfEditPermission Admin
# -----------------------------
@admin.register(models.SelfEditPermission)
class SelfEditPermissionAdmin(admin.ModelAdmin):
    list_display = (
        "employee", "education", "postings", "deputations", "apar", "property",
        "trainings", "awards", "pay", "increments", "leaves", "allegations"
    )
    search_fields = ("employee__hrms_id", "employee__name")


# -----------------------------
# Admin Site Branding
# -----------------------------
admin.site.site_header = "DSTTE SEVA ITIHAS PORTAL"
admin.site.site_title = "DSTTE SEVA ITIHAS PORTAL"
admin.site.index_title = "DSTTE SEVA ITIHAS PORTAL"


from django.utils import timezone

def mark_approved(modeladmin, request, queryset):
    queryset.update(status='APPROVED', approved_by=request.user, approved_at=timezone.now())
mark_approved.short_description = "Mark selected as APPROVED"

def mark_pending(modeladmin, request, queryset):
    queryset.update(status='PENDING', approved_by=None, approved_at=None)
mark_pending.short_description = "Mark selected as PENDING"

def _register_with_approval(Model, base_admin=None, list_fields=None, search=None):
    from django.contrib import admin
    class _A((base_admin or admin.ModelAdmin)):
        list_display = tuple((list_fields or ())) + ('status',)
        actions = [mark_approved, mark_pending]
        search_fields = search or ()
    try:
        admin.site.unregister(Model)
    except Exception:
        pass
    admin.site.register(Model, _A)


try:
    from .models import Education, Posting, Deputation, Apar, PropertyReturn, Training, Award, PayScaleChange, AdvanceIncrement, LeaveRecord, Allegation
    _register_with_approval(Education, list_fields=('employee','degree','year','institution'), search=('employee__hrms_id','degree','institution'))
    _register_with_approval(Posting, list_fields=('employee','college_name','designation','from_date','to_date'), search=('employee__hrms_id','college_name','designation'))
    _register_with_approval(Deputation, list_fields=('employee','college_name','designation','from_date','to_date','place'), search=('employee__hrms_id','college_name','designation','place'))
    _register_with_approval(Apar, list_fields=('employee','year','submitted','submitted_date'), search=('employee__hrms_id','year'))
    _register_with_approval(PropertyReturn, list_fields=('employee','year','submitted','submitted_date'), search=('employee__hrms_id','year'))
    _register_with_approval(Training, list_fields=('employee','area','institute','completion_date'), search=('employee__hrms_id','area','institute'))
    _register_with_approval(Award, list_fields=('employee','name','year','date'), search=('employee__hrms_id','name'))
    _register_with_approval(PayScaleChange, list_fields=('employee','pay_level','start_date','end_date'), search=('employee__hrms_id','pay_level'))
    _register_with_approval(AdvanceIncrement, list_fields=('employee','qualification','passing_year'), search=('employee__hrms_id','qualification'))
    _register_with_approval(LeaveRecord, list_fields=('employee','leave_type','period_from','period_to'), search=('employee__hrms_id','leave_type'))
    _register_with_approval(Allegation, list_fields=('employee','has_allegation'), search=('employee__hrms_id',))
except Exception:
    pass
