# hr/auth_forms.py
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UsernameField
from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _


class HRMSAuthenticationForm(AuthenticationForm):
    """
    Login with a single field named 'username' (labelled 'HRMS ID / Username').
    Tries authenticate(hrms_id=..., password=...) first, then authenticate(username=..., ...).
    """
    username = UsernameField(
        label=_("HRMS ID / Username"),
        widget=forms.TextInput(attrs={
            "autofocus": True,
            "placeholder": "10328222",
            "autocomplete": "username",
            "class": "w-full border border-gray-300 rounded-lg px-3 py-2 "
                "focus:outline-none focus:ring-2 focus:ring-maroon-700",
        })
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "current-password",
            "class": "w-full border border-gray-300 rounded-lg px-3 py-2 pr-12 " "focus:outline-none focus:ring-2 focus:ring-maroon-700",
        })
    )

    error_messages = {
        "invalid_login": _("Invalid HRMS ID/Username or password."),
        "inactive": _("This account is inactive."),
    }

    def clean(self):
        # by this point field-level cleaning has run; use cleaned_data
        ident = (self.cleaned_data.get("username") or "").strip()
        pwd   = self.cleaned_data.get("password") or ""

        if not ident or not pwd:
            raise forms.ValidationError(self.error_messages["invalid_login"], code="invalid_login")

        user = None

        # 1) Try custom backend that accepts hrms_id=...
        try:
            user = authenticate(self.request, hrms_id=ident, password=pwd)
        except TypeError:
            # backend may not accept hrms_id kwarg — ignore
            user = None

        # 2) Fallback: normal username
        if user is None:
            user = authenticate(self.request, username=ident, password=pwd)

        if user is None:
            raise forms.ValidationError(self.error_messages["invalid_login"], code="invalid_login")

        self.confirm_login_allowed(user)
        self.user_cache = user
        return self.cleaned_data
