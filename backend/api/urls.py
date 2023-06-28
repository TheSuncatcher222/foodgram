from django.urls import include, path

from api.v1.urls import urlpatterns as api_v1_urlpatterns

urlpatterns = [
    path('v1/', include(api_v1_urlpatterns)),
]
