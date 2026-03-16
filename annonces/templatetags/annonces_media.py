from django import template


register = template.Library()


@register.filter
def media_src(value):
    if not value:
        return ""

    if isinstance(value, str):
        return value if value.startswith(("http://", "https://")) else value

    url = getattr(value, "url", "")
    if isinstance(url, str) and url.startswith(("http://", "https://")):
        return url

    return url or str(value)
