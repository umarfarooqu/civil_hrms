from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='add_class')
def add_class(field, css):
    """Append CSS classes to a bound field's widget without losing existing ones."""
    try:
        existing = field.field.widget.attrs.get('class', '')
    except Exception:
        existing = ''
    combined = (existing + ' ' + css).strip() if existing else css
    html = field.as_widget(attrs={**getattr(field.field.widget, 'attrs', {}), 'class': combined})
    return mark_safe(html)
