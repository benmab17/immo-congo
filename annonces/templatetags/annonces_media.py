from django.conf import settings
from django import template


register = template.Library()


@register.filter
def media_src(value):
    if not value:
        return ""

    if isinstance(value, str):
        if value.startswith(("http://", "https://")):
            return value
        if value.startswith("/"):
            return value
        return f"{settings.MEDIA_URL}{value.lstrip('/')}"

    name = getattr(value, "name", "")
    if isinstance(name, str) and name.startswith(("http://", "https://")):
        return name

    url = getattr(value, "url", "")
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        return url

    return url or str(value)
