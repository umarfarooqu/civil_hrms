from django.db import models
import os
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.storage import FileSystemStorage
from django.core.exceptions import ValidationError
from django.utils.text import slugify

STATUS_CHOICES = (('PENDING','Pending'), ('APPROVED','Approved'))

MAX_PHOTO_BYTES = 30 * 1024  # 30 KB

class OverwriteStorage(FileSystemStorage):
    """Overwrite files with the same name instead of appending _1, _2..."""
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            self.delete(name)
        return name


def employee_photo_upload_to(instance, filename):
    """
    Save as: employee_photos/<hrms-id>.<ext>
    - Uses HRMS ID as the filename (slugified)
    - Preserves the original extension (defaults to .jpg)
    """
    _, ext = os.path.splitext(filename)
    ext = (ext or ".jpg").lower()
    safe_hrms = slugify(str(getattr(instance, "hrms_id", "") or "unknown")) or "unknown"
    return f"employee_photos/{safe_hrms}{ext}"



# --- Master: College (used as dropdown) --------------------------------------
class College(models.Model):
    code = models.CharField(max_length=20, unique=True, blank=True, help_text="Short code, e.g., NGP13")
    name = models.CharField(max_length=200, unique=True)
    address = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})" if self.code else self.name


# --- Core: Employee and related models ---------------------------------------
class Employee(models.Model):

    civil_list_no = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name="Civil List No"
    )
    hrms_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    father_name = models.CharField(max_length=120, blank=True)
    gender = models.CharField(max_length=10, choices=[("M","Male"),("F","Female"),("O","Other")], blank=True)
    marital_status = models.CharField(max_length=15, blank=True)
    dob = models.DateField(null=True, blank=True)
    email = models.EmailField(blank=True)
    mobile = models.CharField(max_length=15, blank=True)
    photo = models.ImageField(
        upload_to=employee_photo_upload_to,
        storage=OverwriteStorage(),
        blank=True,
        null=True,
        verbose_name="Employee Photo",
        help_text="JPEG/PNG only, ≤ 30 KB"
    )

    def __str__(self):
        return f"{self.name} ({self.hrms_id})"

    def clean(self):
        """Model-level guard so all save paths (admin, forms, scripts) enforce 30 KB."""
        super().clean()
        f = getattr(self, "photo", None)
        if f and hasattr(f, "size") and f.size > MAX_PHOTO_BYTES:
            raise ValidationError({"photo": "Photo must be ≤ 30 KB."})

    def save(self, *args, **kwargs):
        """
        Overwrite file with same name (storage handles it) AND
        remove previous stored file if filename changes (e.g., extension change).
        Also re-check size for programmatic saves that may skip full_clean().
        """
        old_path = None
        if self.pk:
            try:
                old = Employee.objects.get(pk=self.pk)
                if old.photo and old.photo.name != (self.photo and self.photo.name):
                    old_path = old.photo.name
            except Employee.DoesNotExist:
                pass

        # Safety check for direct programmatic saves (without forms)
        f = getattr(self, "photo", None)
        if f and hasattr(f, "size") and f.size > MAX_PHOTO_BYTES:
            raise ValidationError({"photo": "Photo must be ≤ 30 KB."})

        super().save(*args, **kwargs)

        if old_path and self.photo and self.photo.storage.exists(old_path):
            try:
                self.photo.storage.delete(old_path)
            except Exception:
                pass

    # Home details (kept as text to avoid breaking existing data)
    home_state = models.CharField(max_length=60, blank=True)
    home_district = models.CharField(max_length=60, blank=True)
    pin_code = models.CharField(max_length=10, blank=True)
    permanent_address = models.TextField(blank=True)
    current_address = models.TextField(blank=True)

    # --- NEW: Dropdowns (ForeignKey) while keeping your old text fields ---
    # Old text fields retained: division, college_name, present_posting
    division = models.CharField(max_length=120, blank=True)

    # Dropdown for home/parent institute
    college = models.ForeignKey(
        College, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="employees",
        verbose_name="College"
    )

    # Keep original text column (unchanged) for backward compatibility
    college_name = models.CharField(max_length=200, blank=True)

    # Dropdown for present posting institute
    present_posting_college = models.ForeignKey(
        College, on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="present_postings",
        verbose_name="Present Posting (College)"
    )

    # Keep original text column (unchanged) for backward compatibility
    present_posting = models.CharField(max_length=200, blank=True)

    branch = models.CharField(max_length=120, blank=True)
    current_designation = models.CharField(max_length=120, blank=True)

    bpsc_advt_no = models.CharField(max_length=120, blank=True)
    seniority_overall_rank = models.IntegerField(null=True, blank=True)
    selection_category = models.CharField(max_length=40, blank=True)
    actual_category = models.CharField(max_length=40, blank=True)
    disability_quota = models.BooleanField(default=False)
    disability_details = models.CharField(max_length=200, blank=True)

    appointment_text = models.CharField(max_length=200, blank=True)
    appointment_order_no = models.CharField(max_length=120, blank=True)
    date_joining = models.DateField(null=True, blank=True)
    date_confirmation = models.DateField(null=True, blank=True)
    date_retirement = models.DateField(null=True, blank=True)
    pran_gpf_no = models.CharField(max_length=40, blank=True)

    # Link to Django auth user for login
    user = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='employee_profile')

    def __str__(self):
        return f"{self.name} ({self.hrms_id})"


class Education(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="educations")  # UG/PG/PhD/NET/SET
    degree = models.CharField(max_length=80)
    subject = models.CharField(max_length=200, blank=True)
    year = models.PositiveIntegerField(null=True, blank=True)
    institution = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewer_remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.hrms_id} - {self.degree}"


class Posting(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="postings")
    college_name = models.CharField(max_length=200, blank=True)  # kept as text
    pay_level = models.CharField(max_length=40, blank=True)
    designation = models.CharField(max_length=120, blank=True)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    till_date = models.BooleanField(default=False)
    office_order_no = models.CharField(max_length=120, blank=True)
    office_order_date = models.DateField(null=True, blank=True)
    place = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewer_remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.hrms_id} - {self.designation or 'Posting'}"


class Deputation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="deputations")
    college_name = models.CharField(max_length=200, blank=True)  # kept as text
    pay_level = models.CharField(max_length=40, blank=True)
    designation = models.CharField(max_length=120, blank=True)
    from_date = models.DateField(null=True, blank=True)
    to_date = models.DateField(null=True, blank=True)
    till_date = models.BooleanField(default=False)
    office_order_no = models.CharField(max_length=120, blank=True)
    office_order_date = models.DateField(null=True, blank=True)
    place = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewer_remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.hrms_id} - {self.designation or 'Deputation'}"


class Apar(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="apars")
    year = models.IntegerField()
    submitted_date = models.DateField(null=True, blank=True)
    submitted = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewer_remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.hrms_id} - APAR {self.year}"


class PropertyReturn(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="property_returns")
    year = models.IntegerField()
    submitted_date = models.DateField(null=True, blank=True)
    submitted = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewer_remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.hrms_id} - PR {self.year}"


class Training(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="trainings")
    all_8_modules_done = models.BooleanField(default=False)
    overall_completion_date = models.DateField(null=True, blank=True)
    certificate_no = models.CharField(max_length=120, blank=True)
    area = models.CharField(max_length=200, blank=True)
    institute = models.CharField(max_length=200, blank=True)
    duration_weeks = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    completion_date = models.DateField(null=True, blank=True)
    certificate_no_detail = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewer_remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.hrms_id} - Training"


class Award(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="awards")
    name = models.CharField(max_length=200)
    year = models.IntegerField(null=True, blank=True)
    date = models.DateField(null=True, blank=True)
    remarks = models.CharField(max_length=240, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewer_remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.hrms_id} - {self.name}"


class PayScaleChange(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="pay_changes")
    pay_level = models.CharField(max_length=40)
    notif_no = models.CharField(max_length=120, blank=True)
    notif_date = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    till_date = models.BooleanField(default=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewer_remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.hrms_id} - Pay {self.pay_level}"


class AdvanceIncrement(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="increments")
    qualification = models.CharField(max_length=120)
    passing_year = models.IntegerField(null=True, blank=True)
    notif_no = models.CharField(max_length=120, blank=True)
    notif_date = models.DateField(null=True, blank=True)
    count = models.IntegerField(default=0)
    pay_level = models.CharField(max_length=40, blank=True)
    effective_from = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewer_remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.hrms_id} - Inc {self.count}"


class LeaveRecord(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="leaves")
    leave_type = models.CharField(max_length=80)
    period_from = models.DateField()
    period_to = models.DateField()
    office_order_no = models.CharField(max_length=120, blank=True)
    office_order_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewer_remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.hrms_id} - {self.leave_type}"


class Allegation(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name="allegations")
    has_allegation = models.BooleanField(default=False)
    details = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    approved_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='+')
    approved_at = models.DateTimeField(null=True, blank=True)
    reviewer_remark = models.TextField(blank=True)

    def __str__(self):
        return f"{self.employee.hrms_id} - Allegation"


class SelfEditPermission(models.Model):
    """Per-employee switches that superadmin can set to allow self-edit per module."""
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name="self_edit_perm")
    education = models.BooleanField(default=False)
    postings = models.BooleanField(default=False)
    deputations = models.BooleanField(default=False)
    apar = models.BooleanField(default=False)
    property = models.BooleanField(default=False)
    trainings = models.BooleanField(default=False)
    awards = models.BooleanField(default=False)
    pay = models.BooleanField(default=False)
    increments = models.BooleanField(default=False)
    leaves = models.BooleanField(default=False)
    allegations = models.BooleanField(default=False)

    def __str__(self):
        return f"SelfEditPermission({self.employee.hrms_id})"


# --- Auto-create/sync User for employee login (HRMS ID + default password) ---
@receiver(post_save, sender=Employee)
def ensure_user_for_employee(sender, instance: Employee, created, **kwargs):
    """
    Ensures each Employee has a Django user:
    - username = HRMS ID
    - default password:
        * if DOB available -> DDMMYYYY (e.g., 15011993)
        * else -> 'Ngp@' + last 4 of HRMS (e.g., Ngp@1018)
    - Do NOT overwrite an existing usable password.
    """
    if not instance.hrms_id:
        return

    if instance.user_id:
        # keep username in sync if HRMS ID changes
        if instance.user.username != instance.hrms_id:
            instance.user.username = instance.hrms_id
            instance.user.save(update_fields=["username"])
        return

    user, _ = User.objects.get_or_create(username=instance.hrms_id, defaults={"email": instance.email or ""})

    # Set default password only if user has no usable password (i.e., on first creation)
    if not user.has_usable_password():
        if instance.dob:
            default_pwd = instance.dob.strftime("%d%m%Y")
        else:
            tail = str(instance.hrms_id)[-4:].rjust(4, "0")
            default_pwd = f"Ngp@{tail}"
        user.set_password(default_pwd)

    user.is_active = True
    user.is_staff = False  # employees don't access admin by default
    user.save()

    # link back to employee
    instance.user = user
    instance.save(update_fields=["user"])
