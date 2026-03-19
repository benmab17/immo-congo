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

urlpatterns = [
    path('', include('annonces.urls')),
    path('admin/', admin.site.urls),
    path('sw.js', service_worker, name='service_worker'),
]

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]
