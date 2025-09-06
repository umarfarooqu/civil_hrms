from __future__ import annotations
from django import forms
from django.forms import modelformset_factory

from .models import (
    Education, Posting, Deputation, Apar, PropertyReturn, Training,
    Award, PayScaleChange, AdvanceIncrement, LeaveRecord, Allegation,
    Employee,
)

# Try to use the constant from models.py; fallback to 30 KB if not present.
try:
    from .models import MAX_PHOTO_BYTES
except Exception:
    MAX_PHOTO_BYTES = 30 * 1024  # 30 KB

ALLOWED_CTYPES = {"image/jpeg", "image/jpg", "image/png", "image/pjpeg"}


# -------------------------------------------------
# Employee self-edit (photo only) form
# -------------------------------------------------
class EmployeeSelfEditForm(forms.ModelForm):
    """
    Lets an employee upload/update their photo.
    - Enforces 30 KB max size (mirrors model-level check)
    - Best-effort content-type validation (JPEG/PNG)
    """
    class Meta:
        model = Employee
        fields = ["photo"]  # add more fields here if you want broader self-edit
        widgets = {
            "photo": forms.ClearableFileInput(attrs={
                "class": (
                    "block w-full text-sm "
                    "file:mr-4 file:py-2 file:px-4 "
                    "file:rounded-xl file:border-0 "
                    "file:bg-maroon-700 file:text-white "
                    "hover:file:bg-maroon-800"
                ),
                "accept": "image/jpeg,image/png",
            }),
        }
        help_texts = {
            "photo": "JPEG/PNG only, ≤ 30 KB.",
        }
        labels = {
            "photo": "Upload / Change Photo",
        }

    def clean_photo(self):
        f = self.cleaned_data.get("photo")
        if not f:
            return f

        # size check (UI-friendly error; model also enforces)
        if getattr(f, "size", 0) > MAX_PHOTO_BYTES:
            raise forms.ValidationError("Photo must be ≤ 30 KB.")

        # content-type check (best-effort; some storages may not set it)
        ctype = (getattr(f, "content_type", "") or "").lower()
        if ctype and ctype not in ALLOWED_CTYPES:
            raise forms.ValidationError("Only JPEG or PNG images are allowed.")

        return f


# -------------------------------------------------
# Base form for portal formsets (unchanged)
# -------------------------------------------------
class BaseNoEmployeeForm(forms.ModelForm):
    """Hide/remove the employee field and make DateFields use <input type='date'>."""
    class Meta:
        exclude = ("employee", "status", "submitted_by", "submitted_at", "approved_by", "approved_at",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("employee", None)
        for f in self.fields.values():
            if isinstance(f, forms.DateField):
                f.widget = forms.DateInput(attrs={"type": "date"})


# -------------------------------------------------
# Individual model forms (unchanged)
# -------------------------------------------------
class EducationForm(BaseNoEmployeeForm):
    class Meta(BaseNoEmployeeForm.Meta):
        model = Education
        fields = "__all__"

class PostingForm(BaseNoEmployeeForm):
    class Meta(BaseNoEmployeeForm.Meta):
        model = Posting
        fields = "__all__"

class DeputationForm(BaseNoEmployeeForm):
    class Meta(BaseNoEmployeeForm.Meta):
        model = Deputation
        fields = "__all__"

class AparForm(BaseNoEmployeeForm):
    class Meta(BaseNoEmployeeForm.Meta):
        model = Apar
        fields = "__all__"

class PropertyForm(BaseNoEmployeeForm):
    class Meta(BaseNoEmployeeForm.Meta):
        model = PropertyReturn
        fields = "__all__"

class TrainingForm(BaseNoEmployeeForm):
    class Meta(BaseNoEmployeeForm.Meta):
        model = Training
        fields = "__all__"

class AwardForm(BaseNoEmployeeForm):
    class Meta(BaseNoEmployeeForm.Meta):
        model = Award
        fields = "__all__"

class PayForm(BaseNoEmployeeForm):
    class Meta(BaseNoEmployeeForm.Meta):
        model = PayScaleChange
        fields = "__all__"

class IncrementForm(BaseNoEmployeeForm):
    class Meta(BaseNoEmployeeForm.Meta):
        model = AdvanceIncrement
        fields = "__all__"

class LeaveForm(BaseNoEmployeeForm):
    class Meta(BaseNoEmployeeForm.Meta):
        model = LeaveRecord
        fields = "__all__"

class AllegationForm(BaseNoEmployeeForm):
    class Meta(BaseNoEmployeeForm.Meta):
        model = Allegation
        fields = "__all__"


# -------------------------------------------------
# Formsets (unchanged)
# -------------------------------------------------
EducationFS  = modelformset_factory(Education,        form=EducationForm,  extra=1, can_delete=True)
PostingFS    = modelformset_factory(Posting,          form=PostingForm,    extra=1, can_delete=True)
DeputationFS = modelformset_factory(Deputation,       form=DeputationForm, extra=1, can_delete=True)
AparFS       = modelformset_factory(Apar,             form=AparForm,       extra=1, can_delete=True)
PropertyFS   = modelformset_factory(PropertyReturn,   form=PropertyForm,   extra=1, can_delete=True)
TrainingFS   = modelformset_factory(Training,         form=TrainingForm,   extra=1, can_delete=True)
AwardFS      = modelformset_factory(Award,            form=AwardForm,      extra=1, can_delete=True)
PayFS        = modelformset_factory(PayScaleChange,   form=PayForm,        extra=1, can_delete=True)
IncrementFS  = modelformset_factory(AdvanceIncrement, form=IncrementForm,  extra=1, can_delete=True)
LeaveFS      = modelformset_factory(LeaveRecord,      form=LeaveForm,      extra=1, can_delete=True)
AllegationFS = modelformset_factory(Allegation,       form=AllegationForm, extra=1, can_delete=True)
