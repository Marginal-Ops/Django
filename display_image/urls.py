from django.urls import path
from . import views

urlpatterns = [
    path('', views.dataframe.as_view(), name='dataframe'),
    path('display', views.display_html.as_view(), name='display_html'),
    path('download', views.downloadFile, name='downloadFile')
]
