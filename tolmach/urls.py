from django.conf import settings
from django.conf.urls import patterns, include, url
import tolmach.views as main_views
import translations.views as trans_views

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from dajaxice.core import dajaxice_autodiscover, dajaxice_config
admin.autodiscover()
dajaxice_autodiscover()

PATH = getattr(settings, 'URL_PATH', '')

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'%s' % PATH, include('social.apps.django_app.urls',
        namespace='social')),
    url(r'^i18n/', include('django.conf.urls.i18n')),

    # ajax
    url(dajaxice_config.dajaxice_url, include('dajaxice.urls')),

    # main
    url(r'^$', main_views.index, name='index'),
    url(r'^%slogout/$' % PATH, 'django.contrib.auth.views.logout', {'next_page': '/'}),

    # translations
    url(r'^parse-tmx/$', trans_views.parse_tmx),
    url(r'^projects/$', trans_views.projects),
    url(r'^projects/add/$', trans_views.project_add, name='add_project'),
    url(r'^projects/(?P<proj_id>\d+)/delete/$', trans_views.project_delete, name='delete_project'),
    url(r'^projects/(?P<proj_id>\d+)/invite-user/(?P<us_id>\d+)/$', trans_views.invite_user_to_project, name='add_user_to_project'),
    url(r'^projects/(?P<proj_id>\d+)/remove-user/(?P<us_id>\d+)/$', trans_views.remove_user_from_project, name='remove_user_from_project'),
    url(r'^projects/add-text/$', trans_views.add_text_to_project),
    url(r'^text/(?P<text_id>\d+)/$', trans_views.view_text, name='view_text'),
    url(r'^text/(?P<text_id>\d+)/delete/$', trans_views.delete_text, name='delete_text'),
    url(r'^text/(?P<text_id>\d+)/add-glossary/(?P<glos_id>\d+)/$', trans_views.dev_add_glossary_to_text, name='add_glossary_to_text'),
    url(r'^entry/(?P<ent_id>\d+)/translate/$', trans_views.translate_entry, name='translate_entry'),
    url(r'^entry/(?P<ent_id>\d+)/voteup/$', trans_views.entry_voteup, name='entry_voteup'),
    url(r'^entry/(?P<ent_id>\d+)/votedown/$', trans_views.entry_votedown, name='entry_votedown'),
    url(r'^entry/(?P<ent_id>\d+)/approve/$', trans_views.entry_approve, name='entry_approve'),
    url(r'^api/entry-approve/$', trans_views.entry_approve_ajax, name='entry_approve_ajax'),
    url(r'^api/entry-translate/$', trans_views.translate_entry_ajax, name='translate_entry_ajax'),


    # temporarily added urls for developing purpuses
    url(r'^translate/$', trans_views.translate, name='translate'),
    url(r'^dev-add-text/$', trans_views.dev_add_text_to_project, name='dev_add_text'),
    url(r'^dev-add-glossary/$', trans_views.dev_add_new_glossary),
)
