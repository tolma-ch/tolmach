from django.conf import settings
from django.conf.urls import patterns, include, url
import views as main_views
import translations.views as trans_views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

PATH = getattr(settings, 'URL_PATH', '')

urlpatterns = patterns('',
    #url(r'^translations/$', include('translations.urls')),
    # Examples:
    # url(r'^$', 'tolmach.views.home', name='home'),
    # url(r'^tolmach/', include('tolmach.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    #url('', include('social.apps.django_app.urls', namespace='social')),
    url(r'%s' % PATH, include('social.apps.django_app.urls',
        namespace='social')),
    url(r'^$', main_views.index, name='index'),
    url(r'^profile/$', 'tolmach.views.profile', name='profile'),
    url(r'^%slogout/$' % PATH, 'django.contrib.auth.views.logout', {'next_page': '/'}),

    # translations
    url(r'^projects/$', trans_views.projects),
    url(r'^projects/add/$', trans_views.project_add, name='add_project'),
    url(r'^projects/(?P<id>\d+)/delete/$', trans_views.project_delete, name='delete_project'),
    url(r'^projects/add-text/$', trans_views.add_text_to_project),
    url(r'^text/(?P<text_id>\d+)/$', trans_views.view_text),
)
