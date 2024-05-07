from django.contrib import admin
from django.urls import path
from . import views
from django.conf import settings
from django.views.static import serve
from django.urls import re_path
from django.conf.urls import url
from . import views

print('local urls file')
urlpatterns = [
    url(r'^$', views.hello),
    url(r'^hello', views.hello),
    url(r'^search', views.hello),
    url(r'^detail', views.detail),
    url(r'^medias/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]
