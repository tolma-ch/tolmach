from django.conf import settings
from django.conf.urls import patterns, include, url
import tolmach.views as main_views
import translations.views as trans_views
import translations.views_ajax as trans_ajax

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
    # url(r'^parse-tmx/$', trans_views.parse_tmx),
    url(r'^projects/$', trans_views.projects),
    url(r'^projects/add/$', trans_views.project_add, name='add_project'),
    url(r'^projects/(?P<proj_id>\d+)/$', trans_views.project, name='project'),
    url(r'^projects/(?P<proj_id>\d+)/delete/$', trans_views.project_delete, name='delete_project'),
    url(r'^projects/(?P<proj_id>\d+)/invite-user/(?P<us_id>\d+)/$', trans_views.invite_user_to_project, name='add_user_to_project'),
    url(r'^projects/(?P<proj_id>\d+)/remove-user/(?P<us_id>\d+)/$', trans_views.remove_user_from_project, name='remove_user_from_project'),
    url(r'^projects/add-text/$', trans_views.add_text_to_project),
    url(r'^text/(?P<text_id>\d+)/$', trans_views.view_text, name='view_text'),
    url(r'^text/(?P<text_id>\d+)/delete/$', trans_views.delete_text, name='delete_text'),
    url(r'^entry/(?P<ent_id>\d+)/translate/$', trans_views.translate_entry, name='translate_entry'),
    url(r'^entry/(?P<ent_id>\d+)/voteup/$', trans_views.entry_voteup, name='entry_voteup'),
    url(r'^entry/(?P<ent_id>\d+)/approve/$', trans_views.entry_approve, name='entry_approve'),

    # ajax
    url(r'^api/project-create/$', trans_ajax.create_project_ajax, name='get_entries_ajax'),
    url(r'^api/entry/(?:(?P<action>\w+)/)?$', trans_ajax.entry_ajax, name='entry_action_ajax'),
    url(r'^api/entry-approve/$', trans_ajax.approve_entry_ajax, name='entry_approve_ajax'),
    url(r'^api/entry-disapprove/$', trans_ajax.disapprove_entry_ajax, name='entry_approve_ajax'),
    url(r'^api/entry-translate/$', trans_ajax.translate_entry_ajax, name='translate_entry_ajax'),
    url(r'^api/get-users/$', trans_ajax.get_users_ajax, name='get_users_ajax'),
    url(r'^api/participant/$', trans_ajax.participant_ajax, name='participant_ajax'),
    url(r'^api/text/$', trans_ajax.text_ajax, name='text_ajax'),
    url(r'^api/glossary/$', trans_ajax.glossary_ajax, name='glossary_ajax'),
    url(r'^api/tmx/$', trans_ajax.tmx_ajax, name='tmx_ajax'),
    url(r'^api/ya-translate/$', trans_ajax.yandex_translate_ajax, name='yandex_translate'),
    url(r'^api/tmdb-search/$', trans_ajax.tmdb_search, name='tmdb_search'),

    # temporarily added urls for developing purpuses
    url(r'^dev-add-text/$', trans_views.dev_add_text_to_project, name='dev_add_text'),
    url(r'^dev-add-glossary/$', trans_views.dev_add_new_glossary),
    url(r'^projects/add-tmx/$', trans_views.dev_add_tmx_to_project, name='dev_add_tmx'),
    url(r'^text/(?P<text_id>\d+)/add-glossary/(?P<glos_id>\d+)/$', trans_views.dev_add_glossary_to_text, name='add_glossary_to_text'),
    url(r'^text/(?P<text_id>\d+)/add-tmdb/(?P<tmdb_id>\d+)/$', trans_views.dev_add_tmdb_to_text, name='add_tmdb_to_text')
)
