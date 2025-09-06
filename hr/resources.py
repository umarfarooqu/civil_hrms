# hr/resources.py
from import_export import resources, fields
from import_export.widgets import Widget, BooleanWidget
from datetime import datetime
import re
from .models import Employee

class MultiFormatDateWidget(Widget):
    """
    Robust date parser for import-export:
    - Accepts multiple formats
    - Normalizes various separators (/, -, ., unicode dashes)
    - Treats blanks like '', '-', '--', '---', 'NA', etc. as None
    """
    INPUT_FORMATS = [
        "%d-%m-%Y",  # 15-12-1988
        "%d/%m/%Y",  # 15/12/1988
        "%Y-%m-%d",  # 1988-12-15
        "%m/%d/%Y",  # 12/15/1988
    ]
    BLANKS = {"", "na", "n/a", "null", "none", "-", "--", "---"}

    # normalize all separators to '-' and strip spaces
    SEP_PATTERN = re.compile(r"[\u2010-\u2015\u2212/\.]")  # hyphen-like + slash + dot

    def clean(self, value, row=None, *args, **kwargs):
        if value is None:
            return None
        s = str(value).strip()
        if s.lower() in self.BLANKS:
            return None

        # normalize weird separators to '-' (e.g., 15-12-1988 or 15/12/1988)
        s_norm = self.SEP_PATTERN.sub("-", s)

        for fmt in self.INPUT_FORMATS:
            try:
                # try original then normalized
                try:
                    return datetime.strptime(s, fmt).date()
                except Exception:
                    return datetime.strptime(s_norm, fmt).date()
            except Exception:
                continue

        raise ValueError(f"Date '{value}' did not match accepted formats: {', '.join(self.INPUT_FORMATS)}")

    def render(self, value, obj=None):
        if not value:
            return ""
        return value.strftime("%Y-%m-%d")  # export in ISO

class EmployeeResource(resources.ModelResource):
    dob = fields.Field(column_name="dob", attribute="dob", widget=MultiFormatDateWidget())
    date_joining = fields.Field(column_name="date_joining", attribute="date_joining", widget=MultiFormatDateWidget())
    date_confirmation = fields.Field(column_name="date_confirmation", attribute="date_confirmation", widget=MultiFormatDateWidget())
    date_retirement = fields.Field(column_name="date_retirement", attribute="date_retirement", widget=MultiFormatDateWidget())
    disability_quota = fields.Field(column_name="disability_quota", attribute="disability_quota", widget=BooleanWidget())

    class Meta:
        model = Employee
        import_id_fields = ["hrms_id"]  # use HRMS ID as the import key
        fields = (
            "civil_list_no",
            "hrms_id",
            "name",
            "father_name",
            "gender",
            "marital_status",
            "dob",
            "email",
            "mobile",
            "home_state",
            "home_district",
            "pin_code",
            "permanent_address",
            "current_address",
            "division",
            "college_name",
            "present_posting",
            "branch",
            "current_designation",
            "bpsc_advt_no",
            "seniority_overall_rank",
            "selection_category",
            "actual_category",
            "disability_quota",
            "disability_details",
            "appointment_text",
            "appointment_order_no",
            "date_joining",
            "date_confirmation",
            "date_retirement",
            "pran_gpf_no",
        )
