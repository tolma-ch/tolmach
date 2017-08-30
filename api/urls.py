from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^api/$', views.get_project_info, name='get_project_info'),
]