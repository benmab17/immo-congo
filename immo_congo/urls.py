from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles import finders
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views.static import serve


def service_worker(request):
    sw_path = finders.find("annonces/sw.js")
    if not sw_path:
        return HttpResponse("", content_type="application/javascript")
    with open(sw_path, "r", encoding="utf-8") as sw_file:
        response = HttpResponse(sw_file.read(), content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    return response


def static_text_file(request, relative_path, content_type):
    file_path = finders.find(relative_path)
    if not file_path:
        return HttpResponse("", content_type=content_type, status=404)
    with open(file_path, "r", encoding="utf-8") as static_file:
        return HttpResponse(static_file.read(), content_type=content_type)

urlpatterns = [
    path('', include('annonces.urls')),
    path('admin/', admin.site.urls),
    path('sw.js', service_worker, name='service_worker'),
    path(
        'robots.txt',
        lambda request: static_text_file(request, 'robots.txt', 'text/plain; charset=utf-8'),
        name='robots_txt',
    ),
    path(
        'sitemap.xml',
        lambda request: static_text_file(request, 'sitemap.xml', 'application/xml; charset=utf-8'),
        name='sitemap_xml',
    ),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
